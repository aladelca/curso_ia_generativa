"""
Esquemas de validación de datos usando Pydantic
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date, time


class RideBookingInput(BaseModel):
    """Esquema para validar los datos de entrada de predicción"""
    
    # Campos principales
    date: str = Field(..., description="Fecha del viaje en formato YYYY-MM-DD")
    time: str = Field(..., description="Hora del viaje en formato HH:MM:SS")
    customer_id: str = Field(..., description="ID único del cliente")
    vehicle_type: str = Field(..., description="Tipo de vehículo solicitado")
    pickup_location: str = Field(..., description="Ubicación de recogida")
    drop_location: str = Field(..., description="Ubicación de destino")
    
    # Campos opcionales con valores por defecto
    avg_vtat: Optional[float] = Field(None, description="Tiempo promedio de llegada del vehículo")
    avg_ctat: Optional[float] = Field(None, description="Tiempo promedio de llegada del cliente")
    cancelled_rides_by_customer: Optional[int] = Field(None, description="Viajes cancelados por el cliente")
    cancelled_rides_by_driver: Optional[int] = Field(None, description="Viajes cancelados por el conductor")
    incomplete_rides: Optional[int] = Field(None, description="Viajes incompletos")
    booking_value: Optional[float] = Field(None, description="Valor de la reserva")
    ride_distance: Optional[float] = Field(None, description="Distancia del viaje")
    driver_ratings: Optional[float] = Field(None, ge=1.0, le=5.0, description="Calificación del conductor")
    customer_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Calificación del cliente")
    payment_method: Optional[str] = Field(None, description="Método de pago")
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @validator('time')
    def validate_time(cls, v):
        try:
            datetime.strptime(v, '%H:%M:%S')
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM:SS format')
    
    @validator('vehicle_type')
    def validate_vehicle_type(cls, v):
        valid_types = ['Auto', 'Bike', 'eBike', 'Go Mini', 'Go Sedan', 'Premier Sedan']
        if v not in valid_types:
            raise ValueError(f'Vehicle type must be one of: {valid_types}')
        return v


class PredictionResponse(BaseModel):
    """Esquema para la respuesta de predicción"""
    
    booking_id: str = Field(..., description="ID único de la predicción")
    prediction: int = Field(..., description="Predicción: 0 = Driver Found, 1 = No Driver Found")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de No Driver Found")
    risk_level: str = Field(..., description="Nivel de riesgo: Low, Medium, High")
    message: str = Field(..., description="Mensaje explicativo")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la predicción")
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        valid_levels = ['Low', 'Medium', 'High']
        if v not in valid_levels:
            raise ValueError(f'Risk level must be one of: {valid_levels}')
        return v


class HealthResponse(BaseModel):
    """Esquema para respuesta de salud del API"""
    status: str = Field(..., description="Estado del servicio")
    timestamp: datetime = Field(default_factory=datetime.now)
    model_loaded: bool = Field(..., description="Si el modelo está cargado")
    version: str = Field(default="1.0.0", description="Versión del API")


class BatchPredictionInput(BaseModel):
    """Esquema para predicciones en lote"""
    rides: list[RideBookingInput] = Field(..., description="Lista de viajes para predecir")
    
    @validator('rides')
    def validate_rides_count(cls, v):
        if len(v) == 0:
            raise ValueError('At least one ride must be provided')
        if len(v) > 100:
            raise ValueError('Maximum 100 rides allowed per batch')
        return v


class BatchPredictionResponse(BaseModel):
    """Esquema para respuesta de predicciones en lote"""
    predictions: list[PredictionResponse] = Field(..., description="Lista de predicciones")
    total_processed: int = Field(..., description="Total de viajes procesados")
    high_risk_count: int = Field(..., description="Cantidad de viajes de alto riesgo")
    processing_time_seconds: float = Field(..., description="Tiempo de procesamiento en segundos")
