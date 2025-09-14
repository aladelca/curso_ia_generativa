"""
API FastAPI para predicción de disponibilidad de conductores de Uber
"""
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import time
from typing import List, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar esquemas locales
try:
    # Intentar importación relativa primero
    from .schemas import (
        RideBookingInput, PredictionResponse, HealthResponse,
        BatchPredictionInput, BatchPredictionResponse
    )
    from .prediction import predictor
except ImportError:
    # Para desarrollo/testing directo
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from schemas import (
        RideBookingInput, PredictionResponse, HealthResponse,
        BatchPredictionInput, BatchPredictionResponse
    )
    from prediction import predictor

# Crear app FastAPI
app = FastAPI(
    title="Uber Driver Availability Prediction API",
    description="API para predecir la disponibilidad de conductores de Uber",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
MODEL_PATH = os.getenv("MODEL_PATH", "models/")
MODEL_LOADED = False

@app.on_event("startup")
async def startup_event():
    """
    Eventos de inicio de la aplicación
    """
    global MODEL_LOADED
    
    logger.info("🚀 Iniciando Uber Driver Availability Prediction API")
    
    # Buscar el modelo más reciente
    try:
        if os.path.exists(MODEL_PATH):
            model_files = [f for f in os.listdir(MODEL_PATH) if f.endswith('.joblib')]
            
            if model_files:
                # Usar el archivo más reciente
                latest_model = max(model_files, key=lambda x: os.path.getctime(os.path.join(MODEL_PATH, x)))
                model_file_path = os.path.join(MODEL_PATH, latest_model)
                
                # Cargar modelo
                predictor.load_model(model_file_path)
                MODEL_LOADED = True
                logger.info(f"✅ Modelo cargado exitosamente: {latest_model}")
            else:
                logger.warning("⚠️ No se encontraron modelos en el directorio. API en modo sin modelo.")
        else:
            logger.warning("⚠️ Directorio de modelos no existe. API en modo sin modelo.")
            
    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        MODEL_LOADED = False

@app.get("/", response_model=Dict[str, str])
async def root():
    """
    Endpoint raíz con información básica
    """
    return {
        "message": "Uber Driver Availability Prediction API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Endpoint de verificación de salud del servicio
    """
    try:
        health_info = predictor.health_check()
        
        if health_info['can_predict']:
            return HealthResponse(
                status="healthy",
                model_loaded=health_info['model_loaded'],
                version="1.0.0"
            )
        else:
            return HealthResponse(
                status="degraded - model not available",
                model_loaded=health_info['model_loaded'],
                version="1.0.0"
            )
            
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthResponse(
            status=f"unhealthy - {str(e)}",
            model_loaded=False,
            version="1.0.0"
        )

@app.post("/predict", response_model=PredictionResponse)
async def predict_driver_availability(ride_data: RideBookingInput):
    """
    Predice la disponibilidad de conductores para un viaje individual
    """
    if not MODEL_LOADED or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo no disponible. Contacte al administrador."
        )
    
    try:
        # Convertir Pydantic model a dict
        input_data = ride_data.dict()
        
        # Realizar predicción
        result = predictor.predict_single(input_data)
        
        # Convertir a respuesta Pydantic
        response = PredictionResponse(
            booking_id=result['booking_id'],
            prediction=result['prediction'],
            probability=result['probability'],
            risk_level=result['risk_level'],
            message=result['message'],
            timestamp=result['timestamp']
        )
        
        logger.info(f"Predicción realizada - ID: {result['booking_id']}, Riesgo: {result['risk_level']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error procesando la predicción: {str(e)}"
        )

@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_driver_availability(batch_data: BatchPredictionInput):
    """
    Predice la disponibilidad de conductores para múltiples viajes
    """
    if not MODEL_LOADED or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo no disponible. Contacte al administrador."
        )
    
    try:
        # Convertir lista de Pydantic models a lista de dicts
        input_data = [ride.dict() for ride in batch_data.rides]
        
        # Realizar predicciones en lote
        batch_result = predictor.predict_batch(input_data)
        
        # Convertir resultados a respuestas Pydantic
        predictions = [
            PredictionResponse(
                booking_id=pred['booking_id'],
                prediction=pred['prediction'],
                probability=pred['probability'],
                risk_level=pred['risk_level'],
                message=pred['message'],
                timestamp=pred['timestamp']
            )
            for pred in batch_result['predictions']
        ]
        
        response = BatchPredictionResponse(
            predictions=predictions,
            total_processed=batch_result['total_processed'],
            high_risk_count=batch_result['high_risk_count'],
            processing_time_seconds=batch_result['processing_time_seconds']
        )
        
        logger.info(f"Predicción en lote - {batch_result['total_processed']} viajes, {batch_result['high_risk_count']} alto riesgo")
        
        return response
        
    except Exception as e:
        logger.error(f"Error en predicción en lote: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error procesando las predicciones: {str(e)}"
        )

@app.get("/model/info")
async def get_model_info():
    """
    Obtiene información sobre el modelo cargado
    """
    if not MODEL_LOADED or not predictor.is_loaded:
        return {"status": "No model loaded", "model_loaded": False}
    
    try:
        info = predictor.get_model_info()
        return info
        
    except Exception as e:
        logger.error(f"Error obteniendo info del modelo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo información del modelo: {str(e)}"
        )

@app.post("/explain")
async def explain_prediction(ride_data: RideBookingInput):
    """
    Explica una predicción mostrando las features más importantes
    """
    if not MODEL_LOADED or not predictor.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo no disponible. Contacte al administrador."
        )
    
    try:
        # Convertir Pydantic model a dict
        input_data = ride_data.dict()
        
        # Obtener explicación
        explanation = predictor.get_feature_contribution(input_data, top_n=10)
        
        # También obtener la predicción
        prediction_result = predictor.predict_single(input_data)
        
        return {
            "prediction": {
                "booking_id": prediction_result['booking_id'],
                "prediction": prediction_result['prediction'],
                "probability": prediction_result['probability'],
                "risk_level": prediction_result['risk_level'],
                "message": prediction_result['message']
            },
            "explanation": {
                "top_features": explanation,
                "interpretation": "Features ordenadas por contribución a la predicción"
            }
        }
        
    except Exception as e:
        logger.error(f"Error en explicación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generando explicación: {str(e)}"
        )

@app.get("/stats")
async def get_api_stats():
    """
    Obtiene estadísticas básicas del API
    """
    return {
        "api_version": "1.0.0",
        "model_loaded": MODEL_LOADED,
        "predictor_ready": predictor.is_loaded if predictor else False,
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "batch_predict": "/predict/batch",
            "explain": "/explain",
            "model_info": "/model/info"
        }
    }

# Manejo de errores personalizado
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Error inesperado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Error interno del servidor: {str(exc)}"}
    )

def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """
    Función para ejecutar la API
    """
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    # Ejecutar directamente
    run_api(host="127.0.0.1", port=8000, reload=True)
