from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.AutenticacionySeguridad.mixins.tenant_mixins import TenantViewMixin
from apps.AutenticacionySeguridad.permissions.tenant_rbac import HasComponentPermission
from apps.AutenticacionySeguridad.events.bitacora_events import BitacoraModulo, BitacoraResultado, BitacoraAccion
from ..selectors.servicios_selector import CitaSelector
from ..serializers.citas_serializer import CitaSerializer

class DisponibilidadAgendaView(TenantViewMixin, APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "SERV_CITAS"

    @extend_schema(
        tags=["Agenda"],
        operation_id="agenda_disponibilidad",
        parameters=[
            OpenApiParameter("fecha", type=str, description="Fecha a consultar (YYYY-MM-DD)", required=True),
        ],
        responses={200: CitaSerializer(many=True)},
    )
    def get(self, request):
        fecha = request.query_params.get("fecha")
        if not fecha:
            return Response({"error": "La fecha es requerida."}, status=status.HTTP_400_BAD_REQUEST)

        vet_id = self.get_tenant_id()
        
        # 1. Obtener citas ocupadas para ese día (solo activas)
        citas_ocupadas = CitaSelector.get_citas_by_fecha(vet_id, fecha).filter(
            estado__in=["PENDIENTE", "CONFIRMADA", "COMPLETADA"]
        )
        serializer = CitaSerializer(citas_ocupadas, many=True)

        # 2. Generar slots de disponibilidad (Ej: cada 30 min entre 08:00 y 18:00)
        from datetime import datetime, time, timedelta
        
        HORA_APERTURA = 8
        HORA_CIERRE = 18
        SLOT_MINUTOS = 30
        
        slots_disponibles = []
        current_dt = datetime.combine(datetime.strptime(fecha, "%Y-%m-%d").date(), time(HORA_APERTURA, 0))
        end_dt = datetime.combine(current_dt.date(), time(HORA_CIERRE, 0))
        
        # Validar si es hoy para no mostrar horas pasadas
        now = timezone.localtime()
        
        while current_dt < end_dt:
            slot_inicio = current_dt.time()
            slot_fin = (current_dt + timedelta(minutes=SLOT_MINUTOS)).time()
            
            # No permitir horarios pasados
            if current_dt.date() < now.date() or (current_dt.date() == now.date() and current_dt.time() < now.time()):
                current_dt += timedelta(minutes=SLOT_MINUTOS)
                continue

            # Verificar si el slot choca con alguna cita
            esta_ocupado = False
            for cita in citas_ocupadas:
                if slot_inicio < cita.hora_fin and slot_fin > cita.hora_inicio:
                    esta_ocupado = True
                    break
            
            if not esta_ocupado:
                slots_disponibles.append({
                    "inicio": slot_inicio.strftime("%H:%M"),
                    "fin": slot_fin.strftime("%H:%M")
                })
            
            current_dt += timedelta(minutes=SLOT_MINUTOS)

        # 3. Registrar en bitácora
        self.registrar_bitacora(
            accion=BitacoraAccion.DISPONIBILIDAD_CONSULTADA,
            descripcion=f"Consulta de horarios disponibles para la fecha {fecha}.",
            modulo=BitacoraModulo.AGENDA_DISPONIBILIDAD,
            resultado=BitacoraResultado.EXITO,
            metadatos={
                "fecha_programada": fecha,
                "citas_ocupadas_count": citas_ocupadas.count(),
                "slots_disponibles_count": len(slots_disponibles)
            }
        )

        return Response({
            "fecha": fecha,
            "citas_ocupadas": serializer.data,
            "horarios_disponibles": slots_disponibles,
            "mensaje": "Se muestran horarios ocupados y slots disponibles."
        })

class ValidarConflictoView(TenantViewMixin, APIView):
    permission_classes = [IsAuthenticated, HasComponentPermission]
    rbac_component = "SERV_CITAS"

    @extend_schema(
        tags=["Agenda"],
        parameters=[
            OpenApiParameter("fecha", type=str, required=True),
            OpenApiParameter("hora_inicio", type=str, required=True),
            OpenApiParameter("hora_fin", type=str, required=True),
        ],
    )
    def get(self, request):
        fecha = request.query_params.get("fecha")
        h_ini = request.query_params.get("hora_inicio")
        h_fin = request.query_params.get("hora_fin")

        if not all([fecha, h_ini, h_fin]):
            return Response({"error": "Faltan parámetros."}, status=status.HTTP_400_BAD_REQUEST)

        conflicto = CitaSelector.verificar_conflicto_horario(self.get_tenant_id(), fecha, h_ini, h_fin)
        
        if conflicto:
            self.registrar_bitacora(
                accion=BitacoraAccion.CONFLICTO_HORARIO_DETECTADO,
                descripcion=f"Conflicto de horario detectado para el {fecha} entre {h_ini} y {h_fin}.",
                modulo=BitacoraModulo.AGENDA_DISPONIBILIDAD,
                resultado=BitacoraResultado.FALLO,
                metadatos={"fecha": fecha, "hora_inicio": h_ini, "hora_fin": h_fin}
            )

        return Response({
            "disponible": not conflicto,
            "mensaje": "Horario disponible" if not conflicto else "Horario ocupado"
        })
