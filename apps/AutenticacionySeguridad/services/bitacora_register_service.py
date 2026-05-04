import json
import logging
from typing import Any, Dict, Optional

from django.http import HttpRequest

from ..models.bitacora import Bitacora

logger = logging.getLogger(__name__)


class BitacoraService:
    @staticmethod
    def _to_bytes(payload: Dict[str, Any]) -> bytes:
        return json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def registrar_evento(
        *,
        accion: str,
        descripcion: str = "",
        usuario: Optional[Any] = None,
        request: Optional[HttpRequest] = None,
        modulo: str = "",
        entidad_tipo: str = "",
        entidad_id: str = "",
        resultado: str = "",
        metadatos: Optional[Dict[str, Any]] = None,
        ip: Optional[str] = None,
        user_agent: str = "",
    ) -> Optional[Bitacora]:
        try:
            if request is not None:
                ip = ip or request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
                user_agent = user_agent or request.META.get("HTTP_USER_AGENT", "")

            veterinaria_id = None
            usuario_id = None
            if usuario is not None:
                usuario_id = getattr(usuario, "id_usuario", None)
                veterinaria_id = getattr(usuario, "veterinaria_id", None)

            payload = {
                "accion": accion,
                "descripcion": descripcion,
                "modulo": modulo,
                "entidad_tipo": entidad_tipo,
                "entidad_id": str(entidad_id) if entidad_id is not None else "",
                "resultado": resultado,
                "metadatos": metadatos or {},
                "ip": ip or "",
                "user_agent": user_agent or "",
                "usuario_id": usuario_id,
                "path": getattr(request, "path", "") if request else "",
                "method": getattr(request, "method", "") if request else "",
            }

            return Bitacora.objects.create(
                veterinaria_id=veterinaria_id,
                payload=BitacoraService._to_bytes(payload),
            )
        except Exception:
            logger.exception("No se pudo registrar evento en bitacora")
            return None

    @staticmethod
    def registrar_login_exitoso(request: HttpRequest, usuario: Any) -> Optional[Bitacora]:
        return BitacoraService.registrar_evento(
            accion="LOGIN",
            descripcion="Inicio de sesión exitoso.",
            usuario=usuario,
            request=request,
            modulo="autenticacion",
            resultado="EXITO",
        )

    @staticmethod
    def registrar_login_fallido(request: Optional[HttpRequest], identificador: str = "") -> Optional[Bitacora]:
        return BitacoraService.registrar_evento(
            accion="LOGIN_FALLIDO",
            descripcion=f"Intento de inicio de sesión fallido. Identificador: {identificador}",
            request=request,
            modulo="autenticacion",
            resultado="FALLO",
            metadatos={"identificador": identificador},
        )

    @staticmethod
    def registrar_logout(request: HttpRequest, usuario: Any) -> Optional[Bitacora]:
        return BitacoraService.registrar_evento(
            accion="LOGOUT",
            descripcion="Cierre de sesión exitoso.",
            usuario=usuario,
            request=request,
            modulo="autenticacion",
            resultado="EXITO",
        )

    @staticmethod
    def registrar_acceso_denegado(
        request: Optional[HttpRequest],
        descripcion: str = "Intento de acceso denegado.",
        usuario: Optional[Any] = None,
        modulo: str = "sistema",
        metadatos: Optional[Dict[str, Any]] = None,
    ) -> Optional[Bitacora]:
        return BitacoraService.registrar_evento(
            accion="ACCESO_DENEGADO",
            descripcion=descripcion,
            usuario=usuario,
            request=request,
            modulo=modulo,
            resultado="FALLO",
            metadatos=metadatos,
        )
