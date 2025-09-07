"""
Script para ejecutar tests
"""
import os
import sys
import subprocess

def main():
    """Función principal para ejecutar tests"""
    try:
        print("🧪 Ejecutando tests del sistema...")
        print("=" * 50)
        
        # Verificar si pytest está disponible
        try:
            import pytest
        except ImportError:
            print("❌ pytest no está instalado")
            print("   Instala con: pip install pytest")
            return
        
        # Agregar src al path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Ejecutar tests
        test_args = [
            "tests/",
            "-v",
            "--tb=short",
            "-x"  # Stop en el primer error
        ]
        
        result = pytest.main(test_args)
        
        if result == 0:
            print("\n✅ Todos los tests pasaron exitosamente!")
        else:
            print(f"\n❌ Algunos tests fallaron (código: {result})")
            
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")

if __name__ == "__main__":
    main()
