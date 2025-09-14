#!/usr/bin/env python3
"""
Script de entrenamiento para ECS
"""
import os
import sys
import logging
from datetime import datetime

# Agregar src al path
sys.path.append('/app/src')

from training import entrenar_modelo_desde_csv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal de entrenamiento"""
    try:
        logger.info("🚀 Iniciando entrenamiento en ECS")
        
        # Obtener configuración desde variables de entorno
        data_file = os.getenv('DATA_FILE', '/app/data/ncr_ride_bookings.csv')
        use_safe_features = os.getenv('USE_SAFE_FEATURES', 'true').lower() == 'true'
        
        logger.info(f"📊 Archivo de datos: {data_file}")
        logger.info(f"🔒 Usar features seguras: {use_safe_features}")
        
        # Verificar que el archivo existe
        if not os.path.exists(data_file):
            # Intentar buscar el archivo en ubicaciones alternativas
            alternative_paths = [
                '/app/uber/data/ncr_ride_bookings.csv',
                '/app/data/uber/data/ncr_ride_bookings.csv',
                '/app/curso_ia_generativa/uber/data/ncr_ride_bookings.csv'
            ]
            
            data_file = None
            for path in alternative_paths:
                if os.path.exists(path):
                    data_file = path
                    logger.info(f"📍 Archivo encontrado en: {data_file}")
                    break
            
            if data_file is None:
                # Lista archivos disponibles para debug
                logger.error("📁 Archivos disponibles en /app:")
                for root, dirs, files in os.walk('/app'):
                    for file in files:
                        if file.endswith('.csv'):
                            logger.info(f"   📄 {os.path.join(root, file)}")
                
                raise FileNotFoundError(f"Archivo de datos no encontrado en ninguna ubicación")
        
        # Entrenar modelo (se guarda automáticamente en S3)
        logger.info("🤖 Iniciando entrenamiento del modelo...")
        model_path = entrenar_modelo_desde_csv(
            csv_file=data_file,
            model_output_dir="models/",  # Local backup
            use_safe_features_only=use_safe_features
        )
        
        logger.info(f"✅ Entrenamiento completado. Modelo: {model_path}")
        
        # Imprimir información de éxito para ECS logs
        print(f"SUCCESS: Model trained and saved to {model_path}")
        
    except Exception as e:
        logger.error(f"❌ Error en entrenamiento: {e}")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
