# 🚀 Guía de Inicio Rápido - Uber Driver Availability Prediction

## 📋 Resumen del Proyecto

Has creado exitosamente un sistema completo de predicción de disponibilidad de conductores de Uber basado en el análisis del notebook `exploracion.ipynb`. El sistema incluye:

### 🎯 Modelo Final Seleccionado
- **Algoritmo**: CatBoost Classifier con Random Undersampling (RUS)
- **Mejor técnica de balanceamiento**: RUS (Random Undersampling) basado en el F1-Score
- **Optimización**: Umbral óptimo usando índice de Youden
- **Features**: 74+ variables incluyendo temporales, geográficas y de comportamiento

### 🏗️ Arquitectura Implementada

```
uber/src/
├── preprocessing.py    # Feature engineering del notebook
├── training.py         # Entrenamiento con RUS + CatBoost
├── prediction.py       # Motor de predicción
├── api.py             # API FastAPI
├── schemas.py         # Validación de datos
└── models/            # Modelos entrenados
```

## ⚡ Inicio Inmediato

### 1. Configuración Automática
```bash
# Ejecutar script de configuración
cd uber/
./setup.sh
```

### 2. Entrenar Modelo
```bash
# Entrenar el modelo basado en el notebook
python train_model_new.py
```

### 3. Ejecutar API
```bash
# Iniciar servidor FastAPI
python run_api.py
```

### 4. Probar Sistema
```bash
# Ejecutar tests de ejemplo
python test_api_example.py
```

## 🔧 Uso del API

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

**Respuesta Esperada:**
```json
{
  "booking_id": "uuid-generado",
  "prediction": 0,
  "probability": 0.25,
  "risk_level": "Low",
  "message": "Alta probabilidad de encontrar conductor",
  "timestamp": "2024-01-15T08:30:00"
}
```

### Predicción en Lote
```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "rides": [
      {"date": "2024-01-15", "time": "08:30:00", "customer_id": "CID1", "vehicle_type": "Auto", "pickup_location": "Khan Market", "drop_location": "CP"},
      {"date": "2024-01-15", "time": "17:45:00", "customer_id": "CID2", "vehicle_type": "Go Sedan", "pickup_location": "Gurgaon", "drop_location": "Noida"}
    ]
  }'
```

## 📊 Endpoints Disponibles

| Endpoint | Descripción | Ejemplo |
|----------|-------------|---------|
| `GET /` | Info básica | `curl http://localhost:8000/` |
| `GET /health` | Estado del servicio | `curl http://localhost:8000/health` |
| `POST /predict` | Predicción individual | Ver ejemplo arriba |
| `POST /predict/batch` | Predicción en lote | Ver ejemplo arriba |
| `POST /explain` | Explicar predicción | Mismo body que `/predict` |
| `GET /model/info` | Info del modelo | `curl http://localhost:8000/model/info` |
| `GET /docs` | Documentación interactiva | Abrir en navegador |

## 🧪 Testing

### Tests Automatizados
```bash
# Ejecutar todos los tests
python run_tests.py

# Tests específicos
pytest tests/test_preprocessing.py -v
pytest tests/test_api.py -v
pytest tests/test_integration.py -v
```

### Test Manual de la API
```bash
# Probar todos los endpoints
python test_api_example.py
```

## 📈 Monitoreo y Validación

### Verificar Estado del Sistema
```bash
# Estado de salud
curl http://localhost:8000/health

# Información del modelo
curl http://localhost:8000/model/info

# Estadísticas generales
curl http://localhost:8000/stats
```

### Métricas Esperadas del Modelo
Basado en el análisis del notebook, el modelo debería lograr:
- **F1-Score**: ~0.77+ (objetivo principal)
- **Precision**: ~0.80+
- **Recall**: ~0.75+
- **ROC-AUC**: ~0.88+

## 🎯 Casos de Uso Principales

### 1. Alto Riesgo - Hora Pico + Área Problemática
```json
{
  "date": "2024-01-15",
  "time": "18:00:00",
  "vehicle_type": "Auto",
  "pickup_location": "Área Remota",
  "drop_location": "Área Lejana"
}
```
**Resultado Esperado**: `risk_level: "High"`, `probability: >0.7`

### 2. Bajo Riesgo - Área Central + Hora Normal
```json
{
  "date": "2024-01-15",
  "time": "14:00:00",
  "vehicle_type": "Auto",
  "pickup_location": "Khan Market",
  "drop_location": "Central Secretariat"
}
```
**Resultado Esperado**: `risk_level: "Low"`, `probability: <0.3`

### 3. Riesgo Medio - Condiciones Mixtas
```json
{
  "date": "2024-01-15",
  "time": "08:30:00",
  "vehicle_type": "Go Sedan",
  "pickup_location": "Gurgaon",
  "drop_location": "Noida"
}
```
**Resultado Esperado**: `risk_level: "Medium"`, `probability: 0.3-0.7`

## 🔍 Análisis de Features Importantes

El modelo considera estas variables clave (basado en el notebook):

### Variables Temporales (Top Priority)
- `es_hora_pico`: Horas 7-9 AM, 17-20 PM
- `es_fin_semana`: Sábados y domingos
- `periodo_dia`: Mañana, Tarde, Noche, Madrugada

### Variables Geográficas
- `pickup_central`: Khan Market, CP, Central Secretariat, Cyber Hub
- `es_ruta_popular`: Rutas entre áreas centrales
- `pickup_problematico`: Áreas con historial de problemas

### Variables de Comportamiento
- `driver_rating_categoria`: Excelente (>4.5), Normal, Bajo (<4.0)
- `customer_rating_categoria`: Similar al conductor
- `cliente_problematico`: Historial de cancelaciones

### Variables de Interacción
- `centro_en_hora_pico`: Pickup central durante hora pico
- `desbalance_demanda_oferta`: Proxy de oferta vs demanda

## 🚨 Troubleshooting Común

### Problema: Modelo no carga
```bash
# Verificar que existe el modelo
ls -la src/models/

# Si no existe, entrenar nuevo modelo
python train_model.py
```

### Problema: API no responde
```bash
# Verificar que está ejecutándose
curl http://localhost:8000/health

# Si no responde, verificar logs y reiniciar
python run_api.py
```

### Problema: Predicciones extrañas
```bash
# Verificar info del modelo
curl http://localhost:8000/model/info

# Revisar explicación de predicción
curl -X POST http://localhost:8000/explain -H "Content-Type: application/json" -d '{"date":"2024-01-15","time":"08:30:00","customer_id":"test","vehicle_type":"Auto","pickup_location":"Khan Market","drop_location":"CP"}'
```

## 📚 Documentación Adicional

- **README.md**: Documentación completa del proyecto
- **API Docs**: http://localhost:8000/docs (documentación interactiva)
- **Notebook Original**: `notebooks/exploracion.ipynb`
- **Tests**: Directorio `tests/` con ejemplos completos

## 🎉 ¡Felicitaciones!

Has implementado exitosamente un sistema de ML completo que:

✅ **Reproduce el mejor modelo del notebook** (CatBoost + RUS)  
✅ **Implementa feature engineering completo** (74+ variables)  
✅ **Despliega con FastAPI** para uso en producción  
✅ **Incluye tests comprehensivos** para calidad de código  
✅ **Maneja validación de datos** con Pydantic  
✅ **Proporciona explicabilidad** con feature importance  
✅ **Optimiza para F1-Score** como métrica principal  

El sistema está listo para usar localmente y puede escalarse a producción con Docker/Kubernetes según necesidades.
