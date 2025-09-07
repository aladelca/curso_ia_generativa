#!/bin/bash

# Script de configuración para el sistema de predicción de conductores Uber

echo "🚀 Configurando entorno para Uber Driver Availability Prediction"
echo "================================================================="

# Verificar Python
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "   Instala Python 3.8+ desde https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "   ✅ Python $PYTHON_VERSION encontrado"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Entorno virtual creado"
else
    echo "   ℹ️  Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate
echo "   ✅ Entorno virtual activado"

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "   ✅ Dependencias instaladas"
else
    echo "   ❌ requirements.txt no encontrado"
    exit 1
fi

# Verificar estructura de directorios
echo "📁 Verificando estructura de directorios..."
mkdir -p src/models
mkdir -p logs
touch src/models/.gitkeep
touch logs/.gitkeep
echo "   ✅ Directorios creados"

# Verificar datos
echo "📊 Verificando datos..."
if [ -f "data/ncr_ride_bookings.csv" ]; then
    echo "   ✅ Archivo de datos encontrado"
    ROWS=$(wc -l < data/ncr_ride_bookings.csv)
    echo "   📈 Filas en dataset: $ROWS"
else
    echo "   ⚠️  Archivo de datos no encontrado en data/ncr_ride_bookings.csv"
    echo "   💡 Asegúrate de tener el archivo CSV en la ubicación correcta"
fi

# Configuración de entorno
echo "⚙️  Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || echo "# Configuración local" > .env
    echo "   ✅ Archivo .env creado"
else
    echo "   ℹ️  Archivo .env ya existe"
fi

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Activar entorno: source venv/bin/activate"
echo "   2. Entrenar modelo: python train_model.py"
echo "   3. Ejecutar API: python run_api.py"
echo "   4. Probar API: python test_api_example.py"
echo ""
echo "📚 Documentación:"
echo "   • README.md - Guía completa"
echo "   • API Docs: http://localhost:8000/docs (después de ejecutar)"
echo ""
echo "🧪 Testing:"
echo "   • Ejecutar tests: python run_tests.py"
echo "   • Tests individuales: pytest tests/test_*.py -v"
