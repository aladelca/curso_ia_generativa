"""
Script de ejemplo para probar la API de predicción
"""
import requests
import json
import time
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test del endpoint de salud"""
    print("🏥 Probando endpoint de salud...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("   ❌ No se puede conectar a la API. ¿Está ejecutándose?")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_single_prediction():
    """Test de predicción individual"""
    print("\n🎯 Probando predicción individual...")
    
    # Datos de ejemplo
    ride_data = {
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
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=ride_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   🎉 Predicción exitosa!")
            print(f"   📋 Booking ID: {result['booking_id']}")
            print(f"   🎯 Predicción: {result['prediction']} ({'No Driver Found' if result['prediction'] == 1 else 'Driver Found'})")
            print(f"   📊 Probabilidad: {result['probability']:.3f}")
            print(f"   ⚠️  Nivel de Riesgo: {result['risk_level']}")
            print(f"   💬 Mensaje: {result['message']}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_batch_prediction():
    """Test de predicción en lote"""
    print("\n📦 Probando predicción en lote...")
    
    # Datos de ejemplo para lote
    batch_data = {
        "rides": [
            {
                "date": "2024-01-15",
                "time": "08:30:00",
                "customer_id": "CID123456",
                "vehicle_type": "Auto",
                "pickup_location": "Khan Market",
                "drop_location": "Central Secretariat"
            },
            {
                "date": "2024-01-15",
                "time": "17:45:00",
                "customer_id": "CID789012",
                "vehicle_type": "Go Sedan",
                "pickup_location": "CP",
                "drop_location": "Gurgaon Sector 29"
            },
            {
                "date": "2024-01-15",
                "time": "22:15:00",
                "customer_id": "CID345678",
                "vehicle_type": "Bike",
                "pickup_location": "Noida Sector 18",
                "drop_location": "Delhi"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/batch",
            json=batch_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   🎉 Predicción en lote exitosa!")
            print(f"   📊 Total procesados: {result['total_processed']}")
            print(f"   ⚠️  Alto riesgo: {result['high_risk_count']}")
            print(f"   ⏱️  Tiempo de procesamiento: {result['processing_time_seconds']:.3f}s")
            
            print(f"   📋 Resultados individuales:")
            for i, pred in enumerate(result['predictions']):
                print(f"      {i+1}. {pred['risk_level']} (prob: {pred['probability']:.3f})")
            
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_explanation():
    """Test del endpoint de explicación"""
    print("\n🔍 Probando explicación de predicción...")
    
    ride_data = {
        "date": "2024-01-15",
        "time": "08:30:00",
        "customer_id": "CID123456",
        "vehicle_type": "Auto",
        "pickup_location": "Khan Market",
        "drop_location": "Central Secretariat"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/explain",
            json=ride_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   🎉 Explicación exitosa!")
            
            pred = result['prediction']
            print(f"   🎯 Predicción: {pred['prediction']} (prob: {pred['probability']:.3f})")
            print(f"   ⚠️  Riesgo: {pred['risk_level']}")
            
            print(f"   📊 Top features importantes:")
            for feature in result['explanation']['top_features'][:5]:
                print(f"      • {feature['feature']}: {feature['importance']:.2f}")
            
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_model_info():
    """Test del endpoint de información del modelo"""
    print("\n🤖 Probando información del modelo...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/model/info")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Info del modelo:")
            print(f"      Estado: {result.get('status', 'N/A')}")
            print(f"      Cargado: {result.get('is_loaded', False)}")
            if result.get('optimal_threshold'):
                print(f"      Umbral óptimo: {result['optimal_threshold']:.3f}")
            if result.get('number_of_features'):
                print(f"      Número de features: {result['number_of_features']}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_invalid_data():
    """Test con datos inválidos"""
    print("\n❌ Probando datos inválidos...")
    
    invalid_data = {
        "date": "invalid-date",
        "time": "invalid-time",
        "customer_id": "",
        "vehicle_type": "Invalid Vehicle",
        "pickup_location": "",
        "drop_location": ""
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 422:
            print(f"   ✅ Validación funcionando correctamente (422 esperado)")
            return True
        else:
            print(f"   ⚠️  Respuesta inesperada: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Función principal para ejecutar todos los tests"""
    print("🚀 PROBANDO API DE PREDICCIÓN DE CONDUCTORES UBER")
    print("=" * 60)
    print(f"🌐 URL Base: {API_BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now()}")
    print()
    
    tests = [
        ("Health Check", test_health),
        ("Predicción Individual", test_single_prediction),
        ("Predicción en Lote", test_batch_prediction),
        ("Explicación", test_explanation),
        ("Info del Modelo", test_model_info),
        ("Datos Inválidos", test_invalid_data)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   ❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
        
        time.sleep(0.5)  # Pequeña pausa entre tests
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS:")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🏆 Total: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
    else:
        print(f"⚠️  {total - passed} test(s) fallaron")
        print("\n💡 Sugerencias:")
        print("   • Verifica que la API esté ejecutándose")
        print("   • Verifica que el modelo esté entrenado y cargado")
        print("   • Revisa los logs de la API para más detalles")

if __name__ == "__main__":
    main()
