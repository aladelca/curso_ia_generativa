#!/bin/bash

# 🚀 Quick Setup Script para AWS Deployment
# Este script te ayuda a configurar rápidamente el proyecto

echo "🚀 Uber ML - AWS Deployment Setup"
echo "=================================="

# Verificar si estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio uber/"
    exit 1
fi

# Verificar si existe el dataset
if [ ! -f "data/ncr_ride_bookings.csv" ]; then
    echo "⚠️  Dataset no encontrado en data/ncr_ride_bookings.csv"
    echo "   Por favor, asegúrate de que el archivo esté en la ubicación correcta"
    echo "   O actualiza la variable DATA_FILE en .env.aws"
fi

# Verificar dependencias
echo "📦 Verificando dependencias..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Instálalo desde: https://docker.com"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI no está instalado (opcional para testing local)"
    echo "   Puedes instalarlo desde: https://aws.amazon.com/cli/"
fi

echo "✅ Dependencias verificadas"

# Crear archivos necesarios si no existen
echo "📁 Creando estructura de archivos..."

mkdir -p data
mkdir -p src/models

# Verificar que el archivo de secrets ejemplo existe
if [ ! -f ".env.aws" ]; then
    echo "❌ Archivo .env.aws no encontrado"
    exit 1
fi

echo "📝 Configuración de GitHub Secrets"
echo "=================================="
echo "Para completar el setup, necesitas configurar estos secrets en GitHub:"
echo ""
echo "1. Ve a tu repositorio en GitHub"
echo "2. Settings → Secrets and variables → Actions"
echo "3. Añade estos secrets:"
echo ""
echo "   AWS_ACCESS_KEY_ID     = tu_access_key_aquí"
echo "   AWS_SECRET_ACCESS_KEY = tu_secret_key_aquí"
echo ""

# Mostrar información sobre workflows
echo "🔄 Workflows Disponibles"
echo "========================"
echo ""
echo "📋 Training Pipeline (.github/workflows/train.yml):"
echo "   • Trigger: Push a main/master o manual"
echo "   • Construye imagen Docker"
echo "   • Ejecuta entrenamiento en ECS"
echo "   • Guarda modelo en S3"
echo ""
echo "🚀 Prediction Pipeline (.github/workflows/deploy-lambda.yml):"
echo "   • Trigger: Push a main/master o manual"
echo "   • Despliega función Lambda"
echo "   • Configura API Gateway"
echo "   • Ejecuta tests automáticos"
echo ""

echo "🧪 Testing Local"
echo "================"
echo "Para probar localmente antes del deploy:"
echo ""
echo "# Instalar dependencias"
echo "pip install -r requirements.txt"
echo ""
echo "# Test entrenamiento"
echo "python train_model_new.py"
echo ""
echo "# Test predicción"
echo "python -c \"from src.prediction import UberDriverPredictor; predictor = UberDriverPredictor(); print('✅ Imports OK')\""
echo ""

echo "💡 Próximos Pasos"
echo "=================="
echo "1. ✅ Configurar GitHub Secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"
echo "2. 🔄 Hacer push al repositorio para activar workflows"
echo "3. 👀 Monitorear la ejecución en GitHub Actions"
echo "4. 🧪 Probar endpoints cuando el deploy termine"
echo ""

echo "📚 Documentación completa: AWS_DEPLOYMENT.md"
echo ""
echo "🎉 Setup completado! Revisa la documentación para más detalles."
