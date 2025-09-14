# Sistema de Predicción de Disponibilidad de Conductores de Uber

Este sistema implementa un modelo de machine learning para predecir la disponibilidad de conductores de Uber basado en el análisis del notebook `exploracion.ipynb`.

## 🏗️ Arquitectura del Sistema

```
uber/
├── src/                    # Código fuente principal
│   ├── __init__.py
│   ├── preprocessing.py    # Preprocesamiento y feature engineering
│   ├── training.py         # Entrenamiento del modelo
│   ├── prediction.py       # Motor de predicción
│   ├── api.py             # API FastAPI
│   ├── schemas.py         # Esquemas de validación Pydantic
│   └── models/            # Modelos entrenados
├── tests/                 # Tests automatizados
│   ├── test_preprocessing.py
│   ├── test_api.py
│   └── test_integration.py
├── data/                  # Datos originales
├── notebooks/             # Notebooks de exploración
└── requirements.txt       # Dependencias
```

## 🎯 Características del Modelo

### Modelo Base
- **Algoritmo**: CatBoost Classifier
- **Técnica de Balanceamiento**: Random Undersampling (RUS) 
- **Umbral Optimizado**: Índice de Youden para máximo F1-Score
- **Features**: 74+ variables incluyendo temporales, geográficas y de comportamiento

### Métricas Objetivo
- **F1-Score**: Métrica principal para balancear precisión y recall
- **Precisión**: Minimizar falsos positivos
- **Recall**: Maximizar detección de casos "No Driver Found"
- **ROC-AUC**: Capacidad de discriminación general

### Features Principales
- **Temporales**: Hora pico, día de semana, períodos del día
- **Geográficas**: Áreas centrales, rutas populares
- **Comportamiento**: Ratings de cliente/conductor, historial
- **Interacciones**: Combinaciones de factores temporales y geográficos

## 🚀 Inicio Rápido

### 1. Instalación
```bash
# Clonar el repositorio y navegar al directorio
cd uber/

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Entrenar el Modelo
```bash
# Desde el directorio uber/src/
python training.py
```

### 3. Ejecutar la API
```bash
# Desde el directorio uber/src/
python api.py
```

La API estará disponible en: `http://localhost:8000`
- Documentación interactiva: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## 📊 Uso de la API

### Predicción Individual
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "time": "08:30:00",
    "customer_id": "CID123456",
    "vehicle_type": "Auto",
    "pickup_location": "Khan Market",
    "drop_location": "Central Secretariat"
  }'
```

### Predicción en Lote
```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "rides": [
      {
        "date": "2024-01-15",
        "time": "08:30:00",
        "customer_id": "CID123456",
        "vehicle_type": "Auto",
        "pickup_location": "Khan Market",
        "drop_location": "Central Secretariat"
      }
    ]
  }'
```

### Explicación de Predicción
```bash
curl -X POST "http://localhost:8000/explain" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "time": "08:30:00",
    "customer_id": "CID123456",
    "vehicle_type": "Auto",
    "pickup_location": "Khan Market",
    "drop_location": "Central Secretariat"
  }'
```

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_preprocessing.py -v
pytest tests/test_api.py -v
pytest tests/test_integration.py -v
```

### Cobertura de Tests
```bash
# Instalar coverage
pip install pytest-cov

# Ejecutar con cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📋 Endpoints de la API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Información básica de la API |
| `/health` | GET | Estado de salud del servicio |
| `/predict` | POST | Predicción individual |
| `/predict/batch` | POST | Predicción en lote |
| `/explain` | POST | Explicación de predicción |
| `/model/info` | GET | Información del modelo |
| `/stats` | GET | Estadísticas de la API |

## 🔧 Configuración

### Variables de Entorno
```bash
# Archivo .env (opcional)
MODEL_PATH=src/models/
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Configuración del Modelo
El modelo se configura en `training.py`:
- `random_state=42`: Para reproducibilidad
- `iterations=1000`: Número de iteraciones CatBoost
- `learning_rate=0.1`: Tasa de aprendizaje
- `depth=6`: Profundidad del árbol

## 📈 Monitoreo y Logging

### Health Check
```bash
curl http://localhost:8000/health
```

### Métricas del Modelo
```bash
curl http://localhost:8000/model/info
```

### Logs
Los logs se muestran en la consola durante la ejecución. Para producción, configurar logging a archivos.

## 🚀 Deployment

### Usando Gunicorn
```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar
gunicorn src.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Opcional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY data/ data/

EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Estructura de Datos

### Input Schema
```json
{
  "date": "YYYY-MM-DD",
  "time": "HH:MM:SS", 
  "customer_id": "string",
  "vehicle_type": "Auto|Bike|eBike|Go Mini|Go Sedan|Premier Sedan",
  "pickup_location": "string",
  "drop_location": "string",
  "avg_vtat": "float (opcional)",
  "avg_ctat": "float (opcional)",
  "ride_distance": "float (opcional)",
  "driver_ratings": "float 1-5 (opcional)",
  "customer_rating": "float 1-5 (opcional)"
}
```

### Output Schema
```json
{
  "booking_id": "uuid",
  "prediction": "0|1",
  "probability": "float 0-1",
  "risk_level": "Low|Medium|High",
  "message": "string",
  "timestamp": "datetime"
}
```

## 🔄 Pipeline de Desarrollo

1. **Desarrollo**: Modificar código en `src/`
2. **Testing**: `pytest tests/ -v`
3. **Training**: `python src/training.py` 
4. **Validación**: Verificar métricas del modelo
5. **Deployment**: Actualizar API con nuevo modelo

## 🐛 Troubleshooting

### Problemas Comunes

1. **Modelo no carga**
   - Verificar que existe `src/models/*.joblib`
   - Entrenar nuevo modelo con `python src/training.py`

2. **Errores de importación**
   - Verificar `PYTHONPATH` incluye directorio `src/`
   - Instalar dependencias: `pip install -r requirements.txt`

3. **Tests fallan**
   - Verificar estructura de directorios
   - Instalar dependencias de testing: `pip install pytest`

### Logs de Debug
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Referencias

- [Notebook Original](notebooks/exploracion.ipynb)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [CatBoost Documentation](https://catboost.ai/docs/)
- [Imbalanced-learn Documentation](https://imbalanced-learn.org/)

## 🤝 Contribución

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.
