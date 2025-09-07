# 🚀 AWS Deployment Guide

Esta guía explica cómo configurar y desplegar el sistema de predicción de conductores de Uber en AWS usando GitHub Actions.

## 📋 Prerrequisitos

### 1. Cuenta AWS
- Cuenta AWS activa
- Usuario IAM con permisos administrativos
- Access Key y Secret Key generados

### 2. Configuración GitHub
- Repositorio en GitHub
- Permisos para configurar GitHub Secrets

## 🔐 Configuración de GitHub Secrets

Ve a tu repositorio → Settings → Secrets and variables → Actions y configura:

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=abc123...
```

## 🏗️ Arquitectura AWS

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Actions │    │      ECR        │    │      ECS        │
│                 │    │                 │    │                 │
│  Build & Push   ├────┤  Docker Images  ├────┤   Training      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Lambda      │    │      ECR        │    │       S3        │
│                 │    │                 │    │                 │
│  Predictions    ├────┤  Docker Images  ├────┤   ML Models     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Flujos de Trabajo

### Training Pipeline (`train.yml`)
**Trigger:** Push a `main/master` o manual via `workflow_dispatch`

**Pasos:**
1. 🏗️ Build imagen Docker para entrenamiento
2. 📤 Push imagen a ECR
3. ⚙️ Crear/actualizar infraestructura AWS (ECS, S3, IAM)
4. 🚀 Ejecutar tarea ECS de entrenamiento
5. ⏳ Esperar completación del entrenamiento
6. ✅ Verificar modelo subido a S3

**Recursos creados:**
- ECR Repository: `uber-ml-training`
- ECS Cluster: `uber-ml-cluster`
- ECS Task Definition: `uber-ml-training-task`
- S3 Bucket: `uber-ml-models-bucket`
- IAM Role: `ecsTaskExecutionRole`

### Prediction Pipeline (`deploy-lambda.yml`)
**Trigger:** Push a `main/master` o manual via `workflow_dispatch`

**Pasos:**
1. 🏗️ Build imagen Docker para predicción
2. 📤 Push imagen a ECR
3. ⚙️ Crear/actualizar función Lambda
4. 🌐 Configurar API Gateway (opcional)
5. 🧪 Test automático de la función
6. 📝 Generar URLs de acceso

**Recursos creados:**
- ECR Repository: `uber-ml-prediction`
- Lambda Function: `uber-driver-prediction`
- IAM Role: `lambda-execution-role`
- API Gateway: `uber-driver-prediction-api`
- Function URL (acceso directo)

## 💰 Costos Estimados (us-east-1)

### Training (por ejecución)
- **ECS Fargate**: ~$0.05-0.10 (1-2 vCPU, 2-4 GB RAM, 10-30 min)
- **ECR Storage**: ~$0.001/GB/mes
- **S3 Storage**: ~$0.023/GB/mes
- **Data Transfer**: Mínimo

**Total por entrenamiento: ~$0.05-0.15**

### Prediction (por mes, 10K requests)
- **Lambda**: ~$0.20 (10K requests, 1GB RAM, 3s avg)
- **API Gateway**: ~$0.035 (10K requests)
- **S3 GET requests**: ~$0.004
- **ECR Storage**: ~$0.001/GB/mes

**Total mensual (10K requests): ~$0.25**

## 🚀 Proceso de Despliegue

### 1. Primer Despliegue

```bash
# 1. Configurar secrets en GitHub
# 2. Hacer push al repositorio
git add .
git commit -m "feat: setup AWS deployment"
git push origin main

# 3. Los workflows se ejecutarán automáticamente
```

### 2. Entrenar Nuevo Modelo

```bash
# Opción 1: Automático (push cambios)
git add uber/src/
git commit -m "feat: update model features"
git push origin main

# Opción 2: Manual (GitHub UI)
# Ir a Actions → ML Training Pipeline → Run workflow
```

### 3. Actualizar Predictor

```bash
# El predictor se actualiza automáticamente cuando:
# - Se modifica el código de predicción
# - Se hace push a main/master
```

## 🧪 Testing

### Test Local Antes del Deploy
```bash
cd uber

# Test entrenamiento local
python train_model_new.py

# Test predicción local
python -c "
from src.prediction import UberDriverPredictor
predictor = UberDriverPredictor()
predictor.load_model('src/models/uber_driver_model_*.joblib')
result = predictor.predict_single({
    'date': '2024-01-15',
    'time': '08:30:00',
    'customer_id': 'test',
    'vehicle_type': 'Auto',
    'pickup_location': 'Khan Market',
    'drop_location': 'CP'
})
print(result)
"
```

### Test en AWS
```bash
# Después del deploy, usar la Function URL
curl -X POST "https://FUNCTION_URL" \
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

## 📊 Monitoreo

### CloudWatch Logs
- **ECS Training**: `/ecs/uber-ml-training-task`
- **Lambda Prediction**: `/aws/lambda/uber-driver-prediction`

### CloudWatch Metrics
- **Lambda**: Invocations, Duration, Errors
- **ECS**: Task count, CPU/Memory utilization
- **S3**: Number of objects, Bucket size

### Alertas Sugeridas
```bash
# Crear alerta de errores en Lambda
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-Errors-High" \
  --alarm-description "Lambda error rate > 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## 🔧 Troubleshooting

### Training Issues
```bash
# Ver logs de ECS
aws logs describe-log-streams --log-group-name "/ecs/uber-ml-training-task"

# Ver estado de la tarea
aws ecs describe-tasks --cluster uber-ml-cluster --tasks TASK_ARN
```

### Prediction Issues
```bash
# Ver logs de Lambda
aws logs tail "/aws/lambda/uber-driver-prediction" --follow

# Test función directamente
aws lambda invoke --function-name uber-driver-prediction \
  --payload '{"date":"2024-01-15","time":"08:30:00","customer_id":"test","vehicle_type":"Auto","pickup_location":"Khan Market","drop_location":"CP"}' \
  response.json
```

### Permisos Issues
```bash
# Verificar roles IAM
aws iam get-role --role-name ecsTaskExecutionRole
aws iam get-role --role-name lambda-execution-role

# Ver políticas adjuntas
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole
```

## 🧹 Cleanup

### Eliminar Recursos AWS
```bash
# Lambda
aws lambda delete-function --function-name uber-driver-prediction

# ECS
aws ecs delete-service --cluster uber-ml-cluster --service uber-ml-training --force
aws ecs delete-cluster --cluster uber-ml-cluster

# ECR
aws ecr delete-repository --repository-name uber-ml-training --force
aws ecr delete-repository --repository-name uber-ml-prediction --force

# S3 (¡CUIDADO! Esto elimina todos los modelos)
aws s3 rb s3://uber-ml-models-bucket --force

# IAM Roles
aws iam detach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam detach-role-policy --role-name lambda-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name ecsTaskExecutionRole
aws iam delete-role --role-name lambda-execution-role
```

## 📚 Referencias

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [GitHub Actions AWS](https://github.com/aws-actions)
- [Docker Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/)
