"""
Módulo de predicción
"""
import pandas as pd
import numpy as np
import joblib
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Manejar importaciones relativas vs absolutas
try:
    from .preprocessing_seguro import procesar_datos_completo_seguro, preparar_features_para_modelo_seguro
    from .s3_model_manager import s3_model_manager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from preprocessing_seguro import procesar_datos_completo_seguro, preparar_features_para_modelo_seguro
    from s3_model_manager import s3_model_manager


class UberDriverPredictor:
    """
    Predictor para disponibilidad de conductores de Uber
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.optimal_threshold = 0.5
        self.cat_features_indices = None
        self.feature_names = None
        self.is_loaded = False
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str = None, from_s3: bool = True, s3_key: str = None) -> None:
        """
        Carga un modelo previamente entrenado desde S3 o archivo local
        
        Args:
            model_path: Path local del modelo (usado si from_s3=False)
            from_s3: Si True, carga desde S3
            s3_key: Clave específica de S3 (si None, usa el modelo más reciente)
        """
        try:
            if from_s3 and s3_model_manager is not None:
                print(f"📂 Cargando modelo desde S3...")
                
                if s3_key:
                    model_data = s3_model_manager.download_model(s3_key=s3_key)
                elif model_path:
                    # Usar model_path como nombre del modelo en S3
                    model_name = os.path.basename(model_path) if model_path.endswith('.joblib') else f"{model_path}.joblib"
                    model_data = s3_model_manager.download_model(model_name=model_name)
                else:
                    # Cargar el modelo más reciente
                    model_data = s3_model_manager.download_model()
                
            else:
                # Cargar desde archivo local
                if not model_path:
                    raise ValueError("model_path es requerido para carga local")
                
                print(f"📂 Cargando modelo local desde: {model_path}")
                model_data = joblib.load(model_path)
            
            # Asignar datos del modelo
            self.model = model_data['model']
            self.optimal_threshold = model_data['optimal_threshold']
            self.cat_features_indices = model_data['cat_features_indices']
            self.feature_names = model_data['feature_names']
            self.is_loaded = True
            
            print("   ✅ Modelo cargado exitosamente")
            print(f"   Umbral óptimo: {self.optimal_threshold:.3f}")
            print(f"   Features: {len(self.feature_names)}")
            
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            self.is_loaded = False
            raise
    
    def _preprocess_single_input(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocesa una entrada individual
        """
        # Validación básica de datos requeridos
        required_fields = ['date', 'time', 'customer_id', 'vehicle_type', 'pickup_location', 'drop_location']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Convertir a DataFrame
        df = pd.DataFrame([data])
        
        # Procesar datos usando la versión segura
        df_processed = procesar_datos_completo_seguro(df)
        
        # Preparar features para el modelo usando la versión segura
        X, _ = preparar_features_para_modelo_seguro(df_processed, use_safe_features_only=True)
        
        # Asegurar que tenemos todas las features necesarias
        for feature in self.feature_names:
            if feature not in X.columns:
                # Agregar feature faltante con valor por defecto
                if feature in ['avg_vtat', 'avg_ctat', 'ride_distance']:
                    X[feature] = 0.0
                else:
                    X[feature] = 'missing'
        
        # Reordenar columnas para coincidir con el entrenamiento
        X = X[self.feature_names]
        
        return X
    
    def predict_single(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza predicción para una entrada individual
        """
        if not self.is_loaded:
            raise ValueError("Modelo no cargado. Usar load_model() primero.")
        
        try:
            # Preprocesar datos
            X = self._preprocess_single_input(data)
            
            # Realizar predicción
            probability = self.model.predict_proba(X)[0, 1]
            prediction = int(probability >= self.optimal_threshold)
            
            # Determinar nivel de riesgo
            if probability < 0.3:
                risk_level = "Low"
                message = "Alta probabilidad de encontrar conductor"
            elif probability < 0.7:
                risk_level = "Medium"
                message = "Probabilidad moderada de encontrar conductor"
            else:
                risk_level = "High"
                message = "Baja probabilidad de encontrar conductor"
            
            # Crear respuesta
            result = {
                'booking_id': str(uuid.uuid4()),
                'prediction': prediction,
                'probability': float(probability),
                'risk_level': risk_level,
                'message': message,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error en predicción: {str(e)}")
    
    def predict_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Realiza predicciones en lote
        """
        if not self.is_loaded:
            raise ValueError("Modelo no cargado. Usar load_model() primero.")
        
        results = []
        processing_start = datetime.now()
        
        for data in data_list:
            try:
                result = self.predict_single(data)
                results.append(result)
            except Exception as e:
                # En caso de error, agregar resultado con error
                results.append({
                    'booking_id': str(uuid.uuid4()),
                    'prediction': -1,  # Indicador de error
                    'probability': 0.0,
                    'risk_level': "Error",
                    'message': f"Error en predicción: {str(e)}",
                    'timestamp': datetime.now()
                })
        
        processing_time = (datetime.now() - processing_start).total_seconds()
        
        # Agregar estadísticas del lote
        high_risk_count = sum(1 for r in results if r['risk_level'] == 'High')
        
        batch_summary = {
            'predictions': results,
            'total_processed': len(results),
            'high_risk_count': high_risk_count,
            'processing_time_seconds': processing_time
        }
        
        return batch_summary
    
    def get_feature_contribution(self, data: Dict[str, Any], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene la contribución de las features más importantes para una predicción
        """
        if not self.is_loaded:
            raise ValueError("Modelo no cargado. Usar load_model() primero.")
        
        # Preprocesar datos
        X = self._preprocess_single_input(data)
        
        # Obtener importancia de features del modelo
        feature_importance = self.model.get_feature_importance()
        
        # Combinar con valores actuales
        contributions = []
        for i, (feature, importance) in enumerate(zip(self.feature_names, feature_importance)):
            value = X.iloc[0, i]
            contributions.append({
                'feature': feature,
                'value': value,
                'importance': float(importance),
                'contribution_score': float(importance * (1 if isinstance(value, (int, float)) else 0.5))
            })
        
        # Ordenar por contribución y tomar top N
        contributions.sort(key=lambda x: x['contribution_score'], reverse=True)
        
        return contributions[:top_n]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el modelo cargado
        """
        if not self.is_loaded:
            return {
                'status': 'No model loaded',
                'is_loaded': False
            }
        
        return {
            'status': 'Model loaded and ready',
            'is_loaded': True,
            'optimal_threshold': self.optimal_threshold,
            'number_of_features': len(self.feature_names),
            'model_type': type(self.model).__name__,
            'feature_names': self.feature_names[:10] + ['...'] if len(self.feature_names) > 10 else self.feature_names
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado del predictor
        """
        try:
            # Datos de prueba simples
            test_data = {
                'date': '2024-01-01',
                'time': '12:00:00',
                'customer_id': 'TEST123',
                'vehicle_type': 'Auto',
                'pickup_location': 'Khan Market',
                'drop_location': 'CP'
            }
            
            # Intentar predicción
            if self.is_loaded:
                result = self.predict_single(test_data)
                health_status = "Healthy"
                can_predict = True
            else:
                health_status = "Model not loaded"
                can_predict = False
            
            return {
                'status': health_status,
                'model_loaded': self.is_loaded,
                'can_predict': can_predict,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'status': f"Unhealthy: {str(e)}",
                'model_loaded': self.is_loaded,
                'can_predict': False,
                'timestamp': datetime.now()
            }


# Instancia global del predictor (se cargará cuando se inicie la app)
predictor = UberDriverPredictor()
