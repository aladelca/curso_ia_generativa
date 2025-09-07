"""
Gestor de modelos en S3
"""
import os
import joblib
import tempfile
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    NoCredentialsError = Exception
    ClientError = Exception

from .aws_config import aws_config

logger = logging.getLogger(__name__)

class S3ModelManager:
    """Gestor para subir y descargar modelos desde S3"""
    
    def __init__(self):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 operations. Install with: pip install boto3")
        
        self.s3_client = aws_config.get_s3_client()
        self.bucket_name = aws_config.S3_BUCKET
        self.models_prefix = aws_config.S3_MODELS_PREFIX
        
    def upload_model(self, model_data: Dict[str, Any], model_name: str = None) -> str:
        """
        Sube un modelo a S3
        
        Args:
            model_data: Diccionario con el modelo y metadatos
            model_name: Nombre del modelo (opcional, se genera automáticamente)
        
        Returns:
            str: Clave S3 del modelo subido
        """
        try:
            # Generar nombre del modelo si no se proporciona
            if model_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_name = f"uber_driver_model_{timestamp}.joblib"
            
            # Serializar el modelo en memoria
            with tempfile.NamedTemporaryFile() as tmp_file:
                joblib.dump(model_data, tmp_file.name)
                tmp_file.seek(0)
                
                # Subir a S3
                s3_key = f"{self.models_prefix}{model_name}"
                
                logger.info(f"📤 Subiendo modelo a S3: s3://{self.bucket_name}/{s3_key}")
                
                self.s3_client.upload_file(
                    tmp_file.name,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'Metadata': {
                            'model_type': 'catboost_classifier',
                            'created_at': datetime.now().isoformat(),
                            'version': '1.0'
                        }
                    }
                )
                
                logger.info(f"✅ Modelo subido exitosamente a S3")
                return s3_key
                
        except Exception as e:
            logger.error(f"❌ Error subiendo modelo a S3: {e}")
            raise
    
    def download_model(self, s3_key: str = None, model_name: str = None) -> Dict[str, Any]:
        """
        Descarga un modelo desde S3
        
        Args:
            s3_key: Clave completa S3 del modelo
            model_name: Nombre del modelo (se construirá la clave)
        
        Returns:
            Dict: Datos del modelo deserializados
        """
        try:
            # Construir clave S3 si solo se proporciona el nombre
            if s3_key is None and model_name is not None:
                s3_key = f"{self.models_prefix}{model_name}"
            elif s3_key is None and model_name is None:
                # Buscar el modelo más reciente
                s3_key = self.get_latest_model_key()
            
            logger.info(f"📥 Descargando modelo desde S3: s3://{self.bucket_name}/{s3_key}")
            
            # Descargar a archivo temporal
            with tempfile.NamedTemporaryFile() as tmp_file:
                self.s3_client.download_file(
                    self.bucket_name,
                    s3_key,
                    tmp_file.name
                )
                
                # Cargar modelo
                model_data = joblib.load(tmp_file.name)
                
                logger.info(f"✅ Modelo descargado exitosamente desde S3")
                return model_data
                
        except Exception as e:
            logger.error(f"❌ Error descargando modelo desde S3: {e}")
            raise
    
    def get_latest_model_key(self) -> str:
        """
        Obtiene la clave del modelo más reciente en S3
        
        Returns:
            str: Clave S3 del modelo más reciente
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.models_prefix
            )
            
            if 'Contents' not in response:
                raise FileNotFoundError("No models found in S3")
            
            # Ordenar por fecha de modificación (más reciente primero)
            models = sorted(
                response['Contents'],
                key=lambda x: x['LastModified'],
                reverse=True
            )
            
            if not models:
                raise FileNotFoundError("No models found in S3")
            
            latest_key = models[0]['Key']
            logger.info(f"🔍 Modelo más reciente encontrado: {latest_key}")
            
            return latest_key
            
        except Exception as e:
            logger.error(f"❌ Error buscando modelo más reciente: {e}")
            raise
    
    def list_models(self) -> list:
        """
        Lista todos los modelos disponibles en S3
        
        Returns:
            list: Lista de diccionarios con información de modelos
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.models_prefix
            )
            
            if 'Contents' not in response:
                return []
            
            models = []
            for obj in response['Contents']:
                model_info = {
                    'key': obj['Key'],
                    'name': obj['Key'].replace(self.models_prefix, ''),
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                }
                models.append(model_info)
            
            # Ordenar por fecha (más reciente primero)
            models.sort(key=lambda x: x['last_modified'], reverse=True)
            
            return models
            
        except Exception as e:
            logger.error(f"❌ Error listando modelos: {e}")
            raise
    
    def delete_model(self, s3_key: str) -> bool:
        """
        Elimina un modelo de S3
        
        Args:
            s3_key: Clave S3 del modelo a eliminar
        
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            logger.info(f"🗑️  Eliminando modelo: s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"✅ Modelo eliminado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando modelo: {e}")
            return False


# Instancia global
s3_model_manager = S3ModelManager() if BOTO3_AVAILABLE else None
