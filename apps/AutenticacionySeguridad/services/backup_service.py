import logging
import os
import subprocess
import hashlib
from glob import glob
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from io import BytesIO
from shutil import which

from django.conf import settings
from django.db import models

from ..models.backup_restore import BackupRestore
from ..models.backup_config import BackupConfig
from ..models.veterinaria import Veterinaria
from .bitacora_register_service import BitacoraService

logger = logging.getLogger(__name__)


class BackupService:
    """
    Servicio para gestionar backups y restauraciones de PostgreSQL.
    Encapsula lógica de pg_dump, GCS y auditoría.
    """

    @staticmethod
    def create_backup(
        veterinaria_id: int,
        usuario: Any,
        request: Optional[Any] = None,
        motivo: str = "Backup manual",
    ) -> Optional[BackupRestore]:
        """
        Crea un backup manual de la BD para una veterinaria específica.
        Genera archivo SQL, sube a GCS y registra en BackupRestore y BitácoraService.
        """
        try:
            veterinaria = Veterinaria.objects.get(id_veterinaria=veterinaria_id)
            
            # Crear registro en estado INICIADO
            backup_record = BackupRestore.objects.create(
                tipo="BACKUP",
                estado="INICIADO",
                usuario=usuario,
                veterinaria=veterinaria,
                motivo=motivo,
                proveedor_almacenamiento="GCS",
            )

            # Generar nombre del archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{veterinaria.id_veterinaria}_{timestamp}.sql"
            
            # Realizar pg_dump
            try:
                dump_content = BackupService._generate_pg_dump(veterinaria_id)
                
                # Calcular hash
                hash_archivo = hashlib.sha256(dump_content.encode()).hexdigest()
                
                # Subir a GCS
                ruta_remota = BackupService._upload_to_gcs(
                    filename, dump_content, veterinaria_id
                )
                
                # Actualizar registro como exitoso
                backup_record.estado = "EXITOSO"
                backup_record.ruta_archivo = ruta_remota
                backup_record.hash_archivo = hash_archivo
                backup_record.save()
                
                # Actualizar última copia en BackupConfig
                backup_config, _ = BackupConfig.objects.get_or_create(
                    veterinaria_id=veterinaria_id
                )
                backup_config.último_backup = datetime.now()
                backup_config.save()
                
                # Registrar en bitácora
                BitacoraService.registrar_evento(
                    accion="BACKUP_MANUAL_CREADO",
                    descripcion=f"Backup manual creado exitosamente para {veterinaria.nombre}",
                    usuario=usuario,
                    request=request,
                    modulo="backups",
                    entidad_tipo="BackupRestore",
                    entidad_id=str(backup_record.id_backup_restore),
                    resultado="EXITO",
                    metadatos={
                        "veterinaria_id": veterinaria_id,
                        "hash": hash_archivo,
                        "ruta_gcs": ruta_remota,
                        "tamaño_bytes": len(dump_content),
                    }
                )
                
                logger.info(f"Backup exitoso para veterinaria {veterinaria_id}: {filename}")
                return backup_record
                
            except Exception as e:
                backup_record.estado = "FALLIDO"
                backup_record.motivo = f"Error en generación o subida: {str(e)}"
                backup_record.save()
                
                BitacoraService.registrar_evento(
                    accion="BACKUP_MANUAL_FALLIDO",
                    descripcion=f"Fallo al crear backup manual: {str(e)}",
                    usuario=usuario,
                    request=request,
                    modulo="backups",
                    resultado="FALLO",
                    metadatos={
                        "veterinaria_id": veterinaria_id,
                        "error": str(e),
                    }
                )
                
                logger.error(f"Backup fallido para veterinaria {veterinaria_id}: {str(e)}")
                return None
                
        except Veterinaria.DoesNotExist:
            logger.error(f"Veterinaria {veterinaria_id} no encontrada")
            BitacoraService.registrar_evento(
                accion="BACKUP_ERROR",
                descripcion=f"Veterinaria no encontrada: {veterinaria_id}",
                usuario=usuario,
                request=request,
                modulo="backups",
                resultado="FALLO",
            )
            return None
        except Exception as e:
            logger.exception(f"Error inesperado en create_backup: {str(e)}")
            return None

    @staticmethod
    def restore_backup(
        backup_id: int,
        usuario: Any,
        request: Optional[Any] = None,
        motivo: str = "Restauración manual",
    ) -> bool:
        """
        Restaura una BD desde un backup seleccionado.
        Descarga de GCS, inyecta en BD y registra resultado.
        """
        try:
            backup = BackupRestore.objects.get(id_backup_restore=backup_id, tipo="BACKUP")
            
            if backup.estado != "EXITOSO":
                raise ValueError("Solo se pueden restaurar backups exitosos")
            
            # Crear registro de restauración
            restore_record = BackupRestore.objects.create(
                tipo="RESTORE",
                estado="INICIADO",
                usuario=usuario,
                veterinaria=backup.veterinaria,
                motivo=motivo,
                proveedor_almacenamiento="GCS",
            )
            
            try:
                # Descargar de GCS
                dump_content = BackupService._download_from_gcs(backup.ruta_archivo)
                
                # Restaurar en BD
                BackupService._restore_pg_dump(dump_content, backup.veterinaria.id_veterinaria)
                
                # Actualizar registros
                restore_record.estado = "EXITOSO"
                restore_record.hash_archivo = backup.hash_archivo
                restore_record.save()
                
                # Registrar en bitácora
                BitacoraService.registrar_evento(
                    accion="BACKUP_RESTAURADO",
                    descripcion=f"Backup restaurado exitosamente para {backup.veterinaria.nombre}",
                    usuario=usuario,
                    request=request,
                    modulo="backups",
                    entidad_tipo="BackupRestore",
                    entidad_id=str(restore_record.id_backup_restore),
                    resultado="EXITO",
                    metadatos={
                        "veterinaria_id": backup.veterinaria.id_veterinaria,
                        "backup_original_id": backup_id,
                        "fecha_backup_original": str(backup.fecha_hora),
                    }
                )
                
                logger.info(f"Restauración exitosa para veterinaria {backup.veterinaria.id_veterinaria}")
                return True
                
            except Exception as e:
                restore_record.estado = "FALLIDO"
                restore_record.motivo = f"Error en restauración: {str(e)}"
                restore_record.save()
                
                BitacoraService.registrar_evento(
                    accion="BACKUP_RESTAURACION_FALLIDA",
                    descripcion=f"Fallo al restaurar backup: {str(e)}",
                    usuario=usuario,
                    request=request,
                    modulo="backups",
                    resultado="FALLO",
                    metadatos={
                        "veterinaria_id": backup.veterinaria.id_veterinaria,
                        "backup_id": backup_id,
                        "error": str(e),
                    }
                )
                
                logger.error(f"Restauración fallida: {str(e)}")
                return False
                
        except BackupRestore.DoesNotExist:
            logger.error(f"Backup {backup_id} no encontrado o no es de tipo BACKUP")
            BitacoraService.registrar_evento(
                accion="BACKUP_NO_ENCONTRADO",
                descripcion=f"Backup ID {backup_id} no encontrado",
                usuario=usuario,
                request=request,
                modulo="backups",
                resultado="FALLO",
            )
            return False
        except Exception as e:
            logger.exception(f"Error inesperado en restore_backup: {str(e)}")
            return False

    @staticmethod
    def _generate_pg_dump(veterinaria_id: int) -> str:
        """
        Genera un dump SQL de PostgreSQL usando pg_dump.
        Retorna el contenido como string.
        """
        db_url = settings.DATABASES["default"]["ENGINE"]
        db_name = settings.DATABASES["default"]["NAME"]
        db_user = settings.DATABASES["default"]["USER"]
        db_password = settings.DATABASES["default"]["PASSWORD"]
        db_host = settings.DATABASES["default"]["HOST"]
        db_port = settings.DATABASES["default"]["PORT"]

        pg_dump_executable = BackupService._resolve_postgres_executable(
            getattr(settings, "PG_DUMP_PATH", "pg_dump"),
            "pg_dump.exe",
        )

        # Construir comando pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        cmd = [
            pg_dump_executable,
            "-h", db_host or "localhost",
            "-p", str(db_port or 5432),
            "-U", db_user,
            "-F", "p",  # formato plain text
            "-v",
            db_name,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300,  # 5 minutos máximo
                check=True,
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            raise Exception("pg_dump timeout después de 5 minutos")
        except subprocess.CalledProcessError as e:
            raise Exception(f"pg_dump error: {e.stderr}")
        except FileNotFoundError:
            raise Exception(
                f"pg_dump no encontrado en PATH. Revisa PG_DUMP_PATH={pg_dump_executable} "
                "o instala PostgreSQL client tools"
            )

    @staticmethod
    def _restore_pg_dump(dump_content: str, veterinaria_id: int) -> None:
        """
        Restaura un dump SQL en PostgreSQL usando psql.
        """
        db_url = settings.DATABASES["default"]["ENGINE"]
        db_name = settings.DATABASES["default"]["NAME"]
        db_user = settings.DATABASES["default"]["USER"]
        db_password = settings.DATABASES["default"]["PASSWORD"]
        db_host = settings.DATABASES["default"]["HOST"]
        db_port = settings.DATABASES["default"]["PORT"]

        env = os.environ.copy()
        env["PGPASSWORD"] = db_password

        psql_executable = BackupService._resolve_postgres_executable(
            getattr(settings, "PSQL_PATH", "psql"),
            "psql.exe",
        )

        cmd = [
            psql_executable,
            "-h", db_host or "localhost",
            "-p", str(db_port or 5432),
            "-U", db_user,
            "-d", db_name,
            "-v", "ON_ERROR_STOP=on",
        ]

        try:
            result = subprocess.run(
                cmd,
                input=dump_content,
                capture_output=True,
                text=True,
                env=env,
                timeout=600,  # 10 minutos máximo
                check=True,
            )
            logger.info(f"Restauración completada para veterinaria {veterinaria_id}")
        except subprocess.TimeoutExpired:
            raise Exception("psql timeout después de 10 minutos")
        except subprocess.CalledProcessError as e:
            raise Exception(f"psql error: {e.stderr}")
        except FileNotFoundError:
            raise Exception(
                f"psql no encontrado en PATH. Revisa PSQL_PATH={psql_executable} "
                "o instala PostgreSQL client tools"
            )

    @staticmethod
    def _upload_to_gcs(filename: str, content: str, veterinaria_id: int) -> str:
        """
        Sube un archivo a Google Cloud Storage.
        Retorna la ruta remota.
        """
        try:
            bucket_name = getattr(settings, "GCS_BUCKET_NAME", None)
            if not bucket_name:
                raise ValueError("GCS_BUCKET_NAME no configurado en settings")

            client = BackupService._get_storage_client()
            bucket = client.bucket(bucket_name)
            
            # Prefijo por veterinaria para organización
            prefix = getattr(settings, "GCS_BACKUP_PREFIX", "backups")
            blob_name = f"{prefix}/veterinaria_{veterinaria_id}/{filename}"
            blob = bucket.blob(blob_name)
            
            blob.upload_from_string(
                content,
                content_type="text/plain",
                timeout=600,
            )
            
            logger.info(f"Archivo subido a GCS: {blob_name}")
            return blob_name
            
        except Exception as e:
            logger.error(f"Error subiendo a GCS: {str(e)}")
            raise

    @staticmethod
    def _download_from_gcs(blob_path: str) -> str:
        """
        Descarga un archivo desde Google Cloud Storage.
        Retorna el contenido como string.
        """
        try:
            bucket_name = getattr(settings, "GCS_BUCKET_NAME", None)
            if not bucket_name:
                raise ValueError("GCS_BUCKET_NAME no configurado en settings")

            client = BackupService._get_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            content = blob.download_as_string(timeout=600).decode("utf-8")
            logger.info(f"Archivo descargado desde GCS: {blob_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error descargando de GCS: {str(e)}")
            raise

    @staticmethod
    def update_backup_config(
        veterinaria_id: int,
        frecuencia: str,
        dias_retención: int,
        usuario: Any,
        request: Optional[Any] = None,
    ) -> Optional[BackupConfig]:
        """
        Actualiza la configuración de backups automáticos de una veterinaria.
        """
        try:
            config, created = BackupConfig.objects.get_or_create(
                veterinaria_id=veterinaria_id
            )
            
            old_frecuencia = config.frecuencia
            config.frecuencia = frecuencia
            config.dias_retención = dias_retención
            
            # Calcular próximo backup según frecuencia
            config.próximo_backup_programado = BackupService._calculate_next_backup(
                frecuencia
            )
            
            config.save()
            
            # Registrar en bitácora
            BitacoraService.registrar_evento(
                accion="BACKUP_CONFIG_ACTUALIZADA",
                descripcion=f"Configuración de backup actualizada: {old_frecuencia} → {frecuencia}",
                usuario=usuario,
                request=request,
                modulo="backups",
                entidad_tipo="BackupConfig",
                entidad_id=str(config.id_backup_config),
                resultado="EXITO",
                metadatos={
                    "veterinaria_id": veterinaria_id,
                    "frecuencia_anterior": old_frecuencia,
                    "frecuencia_nueva": frecuencia,
                    "días_retención": dias_retención,
                }
            )
            
            logger.info(f"Configuración de backup actualizada para veterinaria {veterinaria_id}")
            return config
            
        except Exception as e:
            logger.error(f"Error actualizando configuración de backup: {str(e)}")
            BitacoraService.registrar_evento(
                accion="BACKUP_CONFIG_ERROR",
                descripcion=f"Error al actualizar config: {str(e)}",
                usuario=usuario,
                request=request,
                modulo="backups",
                resultado="FALLO",
            )
            return None

    @staticmethod
    def _calculate_next_backup(frecuencia: str) -> datetime:
        """
        Calcula la fecha/hora del próximo backup según la frecuencia.
        """
        now = datetime.now()
        
        if frecuencia == "DIARIO":
            return now + timedelta(days=1)
        elif frecuencia == "SEMANAL":
            return now + timedelta(weeks=1)
        elif frecuencia == "MENSUAL":
            return now + timedelta(days=30)
        else:  # PERSONALIZADO o desconocido
            return now + timedelta(weeks=1)  # Default a semanal

    @staticmethod
    def cleanup_old_backups(veterinaria_id: int, days_retention: int) -> int:
        """
        Borra backups más antiguos que días_retention.
        Retorna la cantidad de registros eliminados.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_retention)
            
            old_backups = BackupRestore.objects.filter(
                veterinaria_id=veterinaria_id,
                tipo="BACKUP",
                estado="EXITOSO",
                fecha_hora__lt=cutoff_date,
            )
            
            count = old_backups.count()
            
            # Opcional: eliminar de GCS también
            for backup in old_backups:
                try:
                    BackupService._delete_from_gcs(backup.ruta_archivo)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar de GCS: {backup.ruta_archivo} - {str(e)}")
            
            old_backups.delete()
            logger.info(f"Eliminados {count} backups antiguos para veterinaria {veterinaria_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {str(e)}")
            return 0

    @staticmethod
    def _delete_from_gcs(blob_path: str) -> None:
        """
        Elimina un archivo de Google Cloud Storage.
        """
        try:
            bucket_name = getattr(settings, "GCS_BUCKET_NAME", None)
            if not bucket_name:
                raise ValueError("GCS_BUCKET_NAME no configurado en settings")

            client = BackupService._get_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.delete(timeout=300)
            
            logger.info(f"Archivo eliminado de GCS: {blob_path}")
            
        except Exception as e:
            logger.error(f"Error eliminando de GCS: {str(e)}")
            raise

    @staticmethod
    def _get_storage_client():
        """
        Devuelve un cliente de Google Cloud Storage usando credenciales del entorno.
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError("google-cloud-storage no instalado. Ejecuta: pip install google-cloud-storage")

        project_id = getattr(settings, "GCS_PROJECT_ID", None) or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return storage.Client(project=project_id)

        return storage.Client()

    @staticmethod
    def _resolve_postgres_executable(configured_path: str, executable_filename: str) -> str:
        """
        Resuelve la ruta del ejecutable de PostgreSQL.

        Prioridad:
        1. Ruta configurada en .env
        2. PATH del sistema
        3. Instalaciones típicas en C:\Program Files\PostgreSQL\*\bin
        """
        if configured_path:
            expanded_path = os.path.expandvars(configured_path)
            if os.path.isabs(expanded_path) and os.path.exists(expanded_path):
                return expanded_path
            found_in_path = which(expanded_path)
            if found_in_path:
                return found_in_path

        found_in_path = which(executable_filename)
        if found_in_path:
            return found_in_path

        windows_candidates = glob(r"C:\Program Files\PostgreSQL\*\bin\%s" % executable_filename)
        if windows_candidates:
            return windows_candidates[0]

        raise FileNotFoundError(
            f"No se encontró {executable_filename}. Configura PG_DUMP_PATH/PSQL_PATH con la ruta completa."
        )
