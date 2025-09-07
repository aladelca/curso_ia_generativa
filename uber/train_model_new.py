#!/usr/bin/env python3
"""
Script para entrenar el modelo de disponibilidad de conductores
"""
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """
    Función principal para entrenar el modelo
    """
    print("🚀 Iniciando entrenamiento del modelo...")
    
    try:
        from src.training import entrenar_modelo_desde_csv
        
        # Ruta al dataset
        csv_file = "data/ncr_ride_bookings.csv"
        
        # Verificar que existe el archivo
        if not os.path.exists(csv_file):
            print(f"❌ Error: No se encontró el archivo {csv_file}")
            print("   Asegúrate de que el archivo esté en la ruta correcta")
            return 1
        
        # Entrenar modelo
        model_file = entrenar_modelo_desde_csv(csv_file, "src/models/")
        
        print(f"\n🎉 ¡Entrenamiento completado exitosamente!")
        print(f"📁 Modelo guardado en: {model_file}")
        print(f"🚀 Ahora puedes ejecutar la API con: python run_api.py")
        
        return 0
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Instalar dependencias: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error durante el entrenamiento: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
