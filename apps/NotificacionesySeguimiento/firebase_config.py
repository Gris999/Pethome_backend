import os
import logging
import firebase_admin
from firebase_admin import credentials
from django.conf import settings

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Inicializa el SDK de Firebase Admin usando el archivo JSON de cuenta de servicio.
    """
    try:
        # Si ya está inicializado, no hacer nada
        if firebase_admin._apps:
            return

        # Ruta del JSON de cuenta de servicio:
        # 1) variable de entorno GOOGLE_APPLICATION_CREDENTIALS
        # 2) archivo por defecto en raíz del backend
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.path.join(
            settings.BASE_DIR, "pet-home-25068-firebase-adminsdk-fbsvc-ab68fcca46.json"
        )

        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK inicializado exitosamente.")
        else:
            logger.error(f"No se encontró el archivo de credenciales de Firebase en: {cred_path}")
    except Exception as e:
        logger.error(f"Error al inicializar Firebase Admin SDK: {str(e)}")
