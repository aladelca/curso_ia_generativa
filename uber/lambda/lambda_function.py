"""
Función Lambda para predicciones
"""
import json
import logging
import os
import sys
from typing import Dict, Any

# Agregar src al path
sys.path.append('/var/task/src')

from prediction import UberDriverPredictor

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Instancia global del predictor (se inicializa en cold start)
predictor = None

def init_predictor():
    """Inicializa el predictor cargando el modelo desde S3"""
    global predictor
    
    if predictor is None:
        try:
            logger.info("🔄 Inicializando predictor...")
            predictor = UberDriverPredictor()
            
            # Cargar modelo desde S3 (más reciente por defecto)
            predictor.load_model(from_s3=True)
            
            logger.info("✅ Predictor inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando predictor: {e}")
            raise

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler principal de Lambda
    
    Args:
        event: Evento de Lambda (incluye datos de predicción)
        context: Contexto de Lambda
    
    Returns:
        Dict: Respuesta con predicción o error
    """
    try:
        # Inicializar predictor si no existe
        if predictor is None:
            init_predictor()
        
        # Obtener datos del evento
        if 'body' in event:
            # API Gateway event
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            # Direct invocation
            body = event
        
        logger.info(f"📥 Solicitud de predicción recibida")
        
        # Validar datos requeridos
        required_fields = ['date', 'time', 'customer_id', 'vehicle_type', 'pickup_location', 'drop_location']
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Campos requeridos faltantes: {missing_fields}'
                })
            }
        
        # Realizar predicción
        result = predictor.predict_single(body)
        
        logger.info(f"✅ Predicción exitosa: {result['prediction']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en predicción: {e}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Error interno: {str(e)}'
            })
        }

def lambda_handler_batch(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler para predicciones en lote
    """
    try:
        # Inicializar predictor si no existe
        if predictor is None:
            init_predictor()
        
        # Obtener datos del evento
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        if 'rides' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Campo "rides" requerido para predicciones en lote'
                })
            }
        
        rides = body['rides']
        results = []
        
        logger.info(f"📥 Solicitud de predicción en lote: {len(rides)} viajes")
        
        # Procesar cada viaje
        for i, ride_data in enumerate(rides):
            try:
                result = predictor.predict_single(ride_data)
                result['ride_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Error en viaje {i}: {e}")
                results.append({
                    'ride_index': i,
                    'error': str(e)
                })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'results': results,
                'total_processed': len(results),
                'total_requested': len(rides)
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error en predicción en lote: {e}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Error interno: {str(e)}'
            })
        }
