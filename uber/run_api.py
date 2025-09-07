#!/usr/bin/env python3
"""
Script para ejecutar la API de FastAPI
"""
import sys
import os
import uvicorn

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """
    Función principal para ejecutar la API
    """
    print("🚀 Iniciando API de predicción de conductores...")
    print("📚 Documentación disponible en: http://localhost:8000/docs")
    print("💚 Health check en: http://localhost:8000/health")
    print("🛑 Detener con Ctrl+C")
    print("=" * 60)
    
    try:
        # Cambiar al directorio src para que funcionen las importaciones
        os.chdir(os.path.join(os.path.dirname(__file__), 'src'))
        
        # Ejecutar la API
        uvicorn.run(
            "api:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Instalar dependencias: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error ejecutando la API: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
