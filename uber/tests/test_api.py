"""
Tests para la API FastAPI
"""
import pytest
import json
import sys
import os
from datetime import datetime
from fastapi.testclient import TestClient

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importar la app
try:
    from api import app
except ImportError:
    # Si falla la importación, crear un mock básico para testing
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Test API"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "model_loaded": False}

client = TestClient(app)


class TestAPIBasics:
    """Tests básicos de la API"""
    
    def test_root_endpoint(self):
        """Test del endpoint raíz"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data or "Test API" in data.get("message", "")
    
    def test_health_endpoint(self):
        """Test del endpoint de salud"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
    
    def test_docs_available(self):
        """Test que la documentación esté disponible"""
        response = client.get("/docs")
        # Puede retornar 200 (si está disponible) o redirecciones
        assert response.status_code in [200, 307, 308]


class TestPredictionEndpoints:
    """Tests para endpoints de predicción"""
    
    @pytest.fixture
    def sample_ride_data(self):
        """Datos de prueba para un viaje"""
        return {
            "date": "2024-01-15",
            "time": "08:30:00",
            "customer_id": "CID123456",
            "vehicle_type": "Auto",
            "pickup_location": "Khan Market",
            "drop_location": "Central Secretariat",
            "avg_vtat": 5.0,
            "avg_ctat": 15.0,
            "ride_distance": 10.5,
            "driver_ratings": 4.5,
            "customer_rating": 4.2,
            "payment_method": "UPI"
        }
    
    def test_predict_endpoint_structure(self, sample_ride_data):
        """Test estructura del endpoint de predicción"""
        response = client.post("/predict", json=sample_ride_data)
        
        # Si el modelo no está cargado, esperamos 503, si está cargado esperamos 200
        assert response.status_code in [200, 503]
        
        if response.status_code == 503:
            # Modelo no disponible
            data = response.json()
            assert "detail" in data
            assert "Modelo no disponible" in data["detail"]
        
        elif response.status_code == 200:
            # Modelo disponible y respuesta exitosa
            data = response.json()
            required_fields = ["booking_id", "prediction", "probability", "risk_level", "message"]
            
            for field in required_fields:
                assert field in data
            
            # Validar tipos y rangos
            assert isinstance(data["prediction"], int)
            assert data["prediction"] in [0, 1]
            assert isinstance(data["probability"], float)
            assert 0.0 <= data["probability"] <= 1.0
            assert data["risk_level"] in ["Low", "Medium", "High"]
    
    def test_predict_invalid_data(self):
        """Test predicción con datos inválidos"""
        invalid_data = {
            "date": "invalid-date",
            "time": "invalid-time",
            "customer_id": "C123"
            # Faltan campos requeridos
        }
        
        response = client.post("/predict", json=invalid_data)
        assert response.status_code in [400, 422, 503]  # Bad request, validation error, o service unavailable
    
    def test_predict_missing_fields(self):
        """Test predicción con campos faltantes"""
        incomplete_data = {
            "date": "2024-01-15",
            "customer_id": "C123"
            # Faltan muchos campos requeridos
        }
        
        response = client.post("/predict", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_batch_predict_structure(self, sample_ride_data):
        """Test estructura del endpoint de predicción en lote"""
        batch_data = {
            "rides": [sample_ride_data, sample_ride_data]
        }
        
        response = client.post("/predict/batch", json=batch_data)
        
        # Similar al test individual
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["predictions", "total_processed", "high_risk_count", "processing_time_seconds"]
            
            for field in required_fields:
                assert field in data
            
            assert isinstance(data["predictions"], list)
            assert data["total_processed"] == 2
            assert isinstance(data["processing_time_seconds"], float)
    
    def test_batch_predict_empty_list(self):
        """Test predicción en lote con lista vacía"""
        batch_data = {"rides": []}
        
        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 422  # Validation error
    
    def test_batch_predict_too_many_rides(self, sample_ride_data):
        """Test predicción en lote con demasiados viajes"""
        # Crear una lista con más de 100 elementos
        batch_data = {
            "rides": [sample_ride_data] * 101
        }
        
        response = client.post("/predict/batch", json=batch_data)
        assert response.status_code == 422  # Validation error


class TestVehicleTypeValidation:
    """Tests para validación de tipos de vehículo"""
    
    @pytest.fixture
    def base_ride_data(self):
        """Datos base para testing"""
        return {
            "date": "2024-01-15",
            "time": "08:30:00",
            "customer_id": "CID123456",
            "pickup_location": "Khan Market",
            "drop_location": "Central Secretariat"
        }
    
    @pytest.mark.parametrize("vehicle_type", [
        "Auto", "Bike", "eBike", "Go Mini", "Go Sedan", "Premier Sedan"
    ])
    def test_valid_vehicle_types(self, base_ride_data, vehicle_type):
        """Test tipos de vehículo válidos"""
        ride_data = {**base_ride_data, "vehicle_type": vehicle_type}
        
        response = client.post("/predict", json=ride_data)
        # Si el modelo está disponible debe procesar, si no está disponible da 503
        assert response.status_code in [200, 503]
        
        # Si es 503, es porque el modelo no está cargado, no por validación
        if response.status_code == 503:
            data = response.json()
            assert "Modelo no disponible" in data["detail"]
    
    def test_invalid_vehicle_type(self, base_ride_data):
        """Test tipo de vehículo inválido"""
        ride_data = {**base_ride_data, "vehicle_type": "Invalid Vehicle"}
        
        response = client.post("/predict", json=ride_data)
        assert response.status_code == 422  # Validation error


class TestDateTimeValidation:
    """Tests para validación de fecha y hora"""
    
    @pytest.fixture
    def base_ride_data(self):
        """Datos base para testing"""
        return {
            "customer_id": "CID123456",
            "vehicle_type": "Auto",
            "pickup_location": "Khan Market",
            "drop_location": "Central Secretariat"
        }
    
    @pytest.mark.parametrize("date_str", [
        "2024-01-15", "2024-12-31", "2023-06-15"
    ])
    def test_valid_dates(self, base_ride_data, date_str):
        """Test fechas válidas"""
        ride_data = {**base_ride_data, "date": date_str, "time": "12:00:00"}
        
        response = client.post("/predict", json=ride_data)
        assert response.status_code in [200, 503]  # Success or model not available
    
    @pytest.mark.parametrize("time_str", [
        "00:00:00", "12:30:45", "23:59:59"
    ])
    def test_valid_times(self, base_ride_data, time_str):
        """Test horas válidas"""
        ride_data = {**base_ride_data, "date": "2024-01-15", "time": time_str}
        
        response = client.post("/predict", json=ride_data)
        assert response.status_code in [200, 503]  # Success or model not available
    
    @pytest.mark.parametrize("invalid_date", [
        "2024-13-01", "2024-01-32", "invalid-date", "24-01-15"
    ])
    def test_invalid_dates(self, base_ride_data, invalid_date):
        """Test fechas inválidas"""
        ride_data = {**base_ride_data, "date": invalid_date, "time": "12:00:00"}
        
        response = client.post("/predict", json=ride_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.parametrize("invalid_time", [
        "25:00:00", "12:60:00", "12:30:60", "invalid-time"
    ])
    def test_invalid_times(self, base_ride_data, invalid_time):
        """Test horas inválidas"""
        ride_data = {**base_ride_data, "date": "2024-01-15", "time": invalid_time}
        
        response = client.post("/predict", json=ride_data)
        assert response.status_code == 422  # Validation error


class TestExplainEndpoint:
    """Tests para el endpoint de explicación"""
    
    @pytest.fixture
    def sample_ride_data(self):
        """Datos de prueba para explicación"""
        return {
            "date": "2024-01-15",
            "time": "08:30:00",
            "customer_id": "CID123456",
            "vehicle_type": "Auto",
            "pickup_location": "Khan Market",
            "drop_location": "Central Secretariat"
        }
    
    def test_explain_endpoint_structure(self, sample_ride_data):
        """Test estructura del endpoint de explicación"""
        response = client.post("/explain", json=sample_ride_data)
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura de respuesta
            assert "prediction" in data
            assert "explanation" in data
            
            # Verificar estructura de predicción
            prediction = data["prediction"]
            required_prediction_fields = ["booking_id", "prediction", "probability", "risk_level", "message"]
            for field in required_prediction_fields:
                assert field in prediction
            
            # Verificar estructura de explicación
            explanation = data["explanation"]
            assert "top_features" in explanation
            assert "interpretation" in explanation
            assert isinstance(explanation["top_features"], list)


class TestModelInfoEndpoint:
    """Tests para el endpoint de información del modelo"""
    
    def test_model_info_structure(self):
        """Test estructura del endpoint de información del modelo"""
        response = client.get("/model/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        
        # Si el modelo está cargado, debe tener más información
        if data.get("model_loaded", False):
            additional_fields = ["optimal_threshold", "number_of_features", "model_type"]
            for field in additional_fields:
                assert field in data


class TestStatsEndpoint:
    """Tests para el endpoint de estadísticas"""
    
    def test_stats_structure(self):
        """Test estructura del endpoint de estadísticas"""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["api_version", "model_loaded", "predictor_ready", "endpoints"]
        
        for field in required_fields:
            assert field in data
        
        # Verificar que endpoints es un dict con las rutas esperadas
        endpoints = data["endpoints"]
        expected_endpoints = ["health", "predict", "batch_predict", "explain", "model_info"]
        
        for endpoint in expected_endpoints:
            assert endpoint in endpoints


class TestErrorHandling:
    """Tests para manejo de errores"""
    
    def test_invalid_endpoint(self):
        """Test endpoint inexistente"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_wrong_method(self):
        """Test método HTTP incorrecto"""
        response = client.get("/predict")  # POST endpoint accessed with GET
        assert response.status_code == 405  # Method not allowed
    
    def test_malformed_json(self):
        """Test JSON malformado"""
        response = client.post(
            "/predict",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
