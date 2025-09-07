"""
Módulo de entrenamiento del modelo
"""
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, classification_report,
    confusion_matrix, roc_curve
)
from imblearn.under_sampling import RandomUnderSampler
import warnings
warnings.filterwarnings("ignore")

try:
    from catboost import CatBoostClassifier
except ImportError:
    print("CatBoost no está instalado. Instalar con: pip install catboost")
    CatBoostClassifier = None

# Manejar importaciones relativas vs absolutas
try:
    from .preprocessing_seguro import procesar_datos_completo_seguro, preparar_features_para_modelo_seguro
    from .constants import MODEL_CONFIG, VALIDATION_THRESHOLDS, VALIDATION_TOLERANCE
    from .s3_model_manager import s3_model_manager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from preprocessing_seguro import procesar_datos_completo_seguro, preparar_features_para_modelo_seguro
    from constants import MODEL_CONFIG, VALIDATION_THRESHOLDS, VALIDATION_TOLERANCE
    from s3_model_manager import s3_model_manager


class UberDriverAvailabilityModel:
    """
    Modelo para predecir disponibilidad de conductores de Uber
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = None
        self.cat_features_indices = None
        self.optimal_threshold = 0.5
        self.feature_names = None
        self.scaler = None
        self.is_trained = False
        
    def load_and_preprocess_data(self, file_path: str, use_safe_features: bool = False) -> pd.DataFrame:
        """
        Carga y preprocesa los datos desde CSV
        """
        print(f"📊 Cargando datos desde: {file_path}")
        
        # Cargar datos
        data = pd.read_csv(file_path)
        print(f"   Datos cargados: {data.shape}")
        
        # Procesar datos completo
        data_processed = procesar_datos_completo_seguro(data, use_safe_features_only=use_safe_features)
        print(f"   Datos procesados: {data_processed.shape}")
        
        # Mostrar distribución del target
        if 'target' in data_processed.columns:
            target_dist = data_processed['target'].value_counts()
            print(f"   Distribución target:")
            print(f"     Driver Found (0): {target_dist.get(0, 0)} ({target_dist.get(0, 0)/len(data_processed)*100:.1f}%)")
            print(f"     No Driver Found (1): {target_dist.get(1, 0)} ({target_dist.get(1, 0)/len(data_processed)*100:.1f}%)")
        
        return data_processed
    
    def split_data(self, data: pd.DataFrame, use_safe_features: bool = False, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Divide los datos en conjuntos de entrenamiento y prueba
        """
        print(f"🔀 Dividiendo datos (test_size={test_size})")
        
        # Preparar features
        X, self.cat_features_indices = preparar_features_para_modelo_seguro(data, use_safe_features_only=use_safe_features)
        y = data['target']
        
        # Guardar nombres de features
        self.feature_names = list(X.columns)
        
        # División estratificada
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )
        
        print(f"   Entrenamiento: {X_train.shape[0]} muestras")
        print(f"   Prueba: {X_test.shape[0]} muestras")
        
        return X_train, X_test, y_train, y_test
    
    def apply_random_undersampling(self, X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Aplica Random Undersampling para balancear las clases
        """
        print("📉 Aplicando Random Undersampling...")
        
        rus = RandomUnderSampler(random_state=self.random_state)
        X_resampled, y_resampled = rus.fit_resample(X_train, y_train)
        
        print(f"   Original: {len(X_train)} muestras")
        print(f"   Después de RUS: {len(X_resampled)} muestras")
        print(f"   Distribución después de RUS:")
        print(f"     Clase 0: {sum(y_resampled == 0)} ({sum(y_resampled == 0)/len(y_resampled)*100:.1f}%)")
        print(f"     Clase 1: {sum(y_resampled == 1)} ({sum(y_resampled == 1)/len(y_resampled)*100:.1f}%)")
        
        return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled)
    
    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """
        Entrena el modelo CatBoost
        """
        print("🤖 Entrenando modelo CatBoost...")
        
        if CatBoostClassifier is None:
            raise ImportError("CatBoost no está disponible. Instalar con: pip install catboost")
        
        # Configurar modelo usando constantes
        catboost_params = MODEL_CONFIG['catboost_params']
        self.model = CatBoostClassifier(
            random_state=self.random_state,
            cat_features=self.cat_features_indices,
            **catboost_params
        )
        
        # Entrenar
        self.model.fit(X_train, y_train)
        
        print("   ✅ Modelo entrenado exitosamente")
        self.is_trained = True
    
    def find_optimal_threshold(self, X_test: pd.DataFrame, y_test: pd.Series) -> float:
        """
        Encuentra el umbral óptimo usando el índice de Youden (maximiza TPR - FPR)
        Este método está relacionado con maximizar el área bajo la curva ROC
        """
        print("🎯 Optimizando umbral de decisión usando índice de Youden...")
        
        # Obtener probabilidades
        y_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calcular curva ROC
        fpr, tpr, thresholds = roc_curve(y_test, y_proba)
        
        # Calcular índice de Youden (J = TPR - FPR)
        # El punto óptimo maximiza J = Sensibilidad + Especificidad - 1
        youden_index = tpr - fpr
        
        # Encontrar el umbral que maximiza el índice de Youden
        best_idx = np.argmax(youden_index)
        self.optimal_threshold = thresholds[best_idx]
        
        # Calcular métricas para el umbral óptimo
        y_pred_optimal = (y_proba >= self.optimal_threshold).astype(int)
        f1_optimal = f1_score(y_test, y_pred_optimal)
        precision_optimal = precision_score(y_test, y_pred_optimal)
        recall_optimal = recall_score(y_test, y_pred_optimal)
        
        print(f"   Umbral óptimo (Youden): {self.optimal_threshold:.3f}")
        print(f"   Índice de Youden máximo: {youden_index[best_idx]:.3f}")
        print(f"   TPR (Sensibilidad): {tpr[best_idx]:.3f}")
        print(f"   FPR (1-Especificidad): {fpr[best_idx]:.3f}")
        print(f"   F1-Score en umbral óptimo: {f1_optimal:.3f}")
        print(f"   Precision: {precision_optimal:.3f}")
        print(f"   Recall: {recall_optimal:.3f}")
        
        return self.optimal_threshold
    
    def evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series, use_optimal_threshold: bool = True) -> Dict[str, float]:
        """
        Evalúa el modelo y retorna métricas
        """
        threshold = self.optimal_threshold if use_optimal_threshold else 0.5
        
        print(f"📊 Evaluando modelo (umbral={threshold:.3f})...")
        
        # Predicciones
        y_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= threshold).astype(int)
        
        # Métricas
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_proba),
            'pr_auc': average_precision_score(y_test, y_proba)
        }
        
        # Mostrar resultados
        print("   Resultados:")
        for metric, value in metrics.items():
            print(f"     {metric.upper()}: {value:.3f}")
        
        # Matriz de confusión
        cm = confusion_matrix(y_test, y_pred)
        print("   Matriz de confusión:")
        print("                 Predicho")
        print("                No    Sí")
        print(f"   Real   No    {cm[0,0]:6d} {cm[0,1]:5d}")
        print(f"          Sí    {cm[1,0]:6d} {cm[1,1]:5d}")
        
        return metrics
    
    def validate_model_performance(self, X_test: pd.DataFrame, y_test: pd.Series, 
                                 baseline_metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Valida el rendimiento del modelo y detecta posible drift
        """
        print("\n🔍 VALIDACIÓN Y SEGUIMIENTO DE DESEMPEÑO")
        print("=" * 50)
        
        # Evaluar modelo actual
        current_metrics = self.evaluate_model(X_test, y_test, use_optimal_threshold=True)
        
        # Métricas esperadas basadas en las constantes (más realistas)
        expected_metrics = VALIDATION_THRESHOLDS
        
        # Tolerancias para detectar drift
        tolerance = VALIDATION_TOLERANCE
        
        validation_results = {
            'current_metrics': current_metrics,
            'expected_metrics': expected_metrics,
            'performance_status': 'good',
            'warnings': [],
            'recommendations': []
        }
        
        print("📊 COMPARACIÓN DE MÉTRICAS:")
        print("-" * 30)
        
        # Comparar con métricas esperadas
        for metric, expected_value in expected_metrics.items():
            if metric in current_metrics:
                current_value = current_metrics[metric]
                diff = current_value - expected_value
                diff_pct = (diff / expected_value) * 100
                
                # Estado de la métrica
                if abs(diff) <= tolerance[metric]:
                    status = "✅ BIEN"
                elif diff < -tolerance[metric]:
                    status = "⚠️  BAJO"
                    validation_results['warnings'].append(f"{metric.upper()} por debajo del esperado")
                    if validation_results['performance_status'] == 'good':
                        validation_results['performance_status'] = 'degraded'
                else:
                    status = "🎉 EXCELENTE"
                
                print(f"   {metric.upper():12} | Actual: {current_value:.3f} | Esperado: {expected_value:.3f} | Diff: {diff:+.3f} ({diff_pct:+.1f}%) | {status}")
        
        # Comparar con baseline si se proporciona
        if baseline_metrics:
            print("\n📈 COMPARACIÓN CON BASELINE ANTERIOR:")
            print("-" * 40)
            
            for metric, baseline_value in baseline_metrics.items():
                if metric in current_metrics:
                    current_value = current_metrics[metric]
                    diff = current_value - baseline_value
                    diff_pct = (diff / baseline_value) * 100
                    
                    if abs(diff) <= tolerance.get(metric, 0.05):
                        trend = "➡️  ESTABLE"
                    elif diff > 0:
                        trend = "📈 MEJORA"
                    else:
                        trend = "📉 DEGRADACIÓN"
                        validation_results['warnings'].append(f"{metric.upper()} degradado respecto al baseline")
                    
                    print(f"   {metric.upper():12} | Actual: {current_value:.3f} | Baseline: {baseline_value:.3f} | Diff: {diff:+.3f} ({diff_pct:+.1f}%) | {trend}")
        
        # Generar recomendaciones
        if validation_results['warnings']:
            print("\n⚠️  ADVERTENCIAS DETECTADAS:")
            for warning in validation_results['warnings']:
                print(f"   • {warning}")
            
            print("\n💡 RECOMENDACIONES:")
            if any('f1_score' in w.lower() for w in validation_results['warnings']):
                validation_results['recommendations'].append("Revisar balance de clases y técnicas de resampling")
                print("   • Revisar balance de clases y técnicas de resampling")
            
            if any('precision' in w.lower() for w in validation_results['warnings']):
                validation_results['recommendations'].append("Ajustar umbral de decisión para reducir falsos positivos")
                print("   • Ajustar umbral de decisión para reducir falsos positivos")
            
            if any('recall' in w.lower() for w in validation_results['warnings']):
                validation_results['recommendations'].append("Revisar features relacionadas con detección de casos positivos")
                print("   • Revisar features relacionadas con detección de casos positivos")
            
            if any('roc_auc' in w.lower() for w in validation_results['warnings']):
                validation_results['recommendations'].append("Considerar reentrenamiento con datos más recientes")
                print("   • Considerar reentrenamiento con datos más recientes")
        else:
            print("\n🎉 MODELO DENTRO DE PARÁMETROS ESPERADOS")
        
        # Análisis de distribución de predicciones
        y_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= self.optimal_threshold).astype(int)
        
        # Distribución de probabilidades
        prob_stats = {
            'mean_prob': float(np.mean(y_proba)),
            'std_prob': float(np.std(y_proba)),
            'low_confidence': float(np.sum((y_proba > 0.3) & (y_proba < 0.7)) / len(y_proba)),
            'high_confidence': float(np.sum((y_proba <= 0.3) | (y_proba >= 0.7)) / len(y_proba))
        }
        
        print(f"\n📊 ANÁLISIS DE CONFIANZA EN PREDICCIONES:")
        print(f"   Probabilidad promedio: {prob_stats['mean_prob']:.3f}")
        print(f"   Desviación estándar: {prob_stats['std_prob']:.3f}")
        print(f"   Predicciones de alta confianza: {prob_stats['high_confidence']:.1%}")
        print(f"   Predicciones de baja confianza: {prob_stats['low_confidence']:.1%}")
        
        if prob_stats['low_confidence'] > 0.3:
            validation_results['warnings'].append("Alta proporción de predicciones con baja confianza")
            validation_results['recommendations'].append("Considerar reentrenamiento o ajuste de features")
        
        validation_results['probability_stats'] = prob_stats
        
        return validation_results
    
    def log_training_metrics(self, metrics: Dict[str, float], validation_results: Dict[str, Any], 
                           model_file: str) -> None:
        """
        Registra métricas de entrenamiento en logs estructurados para seguimiento
        """
        import json
        import logging
        
        # Configurar logger específico para métricas
        metrics_logger = logging.getLogger('model_metrics')
        metrics_logger.setLevel(logging.INFO)
        
        # Crear handler para archivo de métricas si no existe
        if not metrics_logger.handlers:
            handler = logging.FileHandler('model_metrics.log')
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            metrics_logger.addHandler(handler)
        
        # Preparar datos para logging
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'model_file': model_file,
            'training_metrics': metrics,
            'validation_status': validation_results['performance_status'],
            'warnings_count': len(validation_results['warnings']),
            'warnings': validation_results['warnings'],
            'recommendations': validation_results['recommendations'],
            'probability_stats': validation_results['probability_stats'],
            'model_config': {
                'algorithm': 'CatBoost',
                'resampling': 'RandomUnderSampling',
                'optimal_threshold': float(self.optimal_threshold),
                'random_state': self.random_state
            }
        }
        
        # Log como JSON para fácil parsing
        metrics_logger.info(json.dumps(log_data, indent=2))
        
        print(f"\n📝 Métricas registradas en: model_metrics.log")
        
        # También mostrar resumen en consola
        print("\n🚀 RESUMEN DE ENTRENAMIENTO:")
        print("=" * 40)
        print(f"   📁 Modelo: {os.path.basename(model_file)}")
        print(f"   🎯 F1-Score: {metrics['f1_score']:.3f}")
        print(f"   📊 Estado: {validation_results['performance_status'].upper()}")
        print(f"   ⚠️  Advertencias: {len(validation_results['warnings'])}")
        
        if validation_results['performance_status'] != 'good':
            print(f"   💡 Recomendaciones: {len(validation_results['recommendations'])}")
    
    def train_complete_pipeline(self, file_path: str, baseline_metrics: Optional[Dict[str, float]] = None, 
                               use_safe_features: bool = False, model_output_dir: str = "models/") -> Dict[str, float]:
        """
        Pipeline completo de entrenamiento con validación y seguimiento
        
        Args:
            file_path: Path al archivo CSV
            baseline_metrics: Métricas baseline para comparación
            use_safe_features: Si True, usa solo features seguras sin data leakage
            model_output_dir: Directorio donde guardar el modelo
        """
        mode_text = "SEGURO (sin data leakage)" if use_safe_features else "COMPLETO"
        print(f"🚀 INICIANDO PIPELINE DE ENTRENAMIENTO {mode_text}")
        print("=" * 60)
        
        # 1. Cargar y procesar datos
        data = self.load_and_preprocess_data(file_path, use_safe_features)
        
        # 2. Dividir datos
        X_train, X_test, y_train, y_test = self.split_data(data, use_safe_features)
        
        # 3. Aplicar Random Undersampling
        X_train_balanced, y_train_balanced = self.apply_random_undersampling(X_train, y_train)
        
        # 4. Entrenar modelo
        self.train_model(X_train_balanced, y_train_balanced)
        
        # 5. Optimizar umbral
        self.find_optimal_threshold(X_test, y_test)
        
        # 6. Evaluar modelo
        metrics = self.evaluate_model(X_test, y_test, use_optimal_threshold=True)
        
        # 7. NUEVO: Validación y seguimiento de desempeño
        validation_results = self.validate_model_performance(X_test, y_test, baseline_metrics)
        
        # 8. NUEVO: Guardar modelo (usando el directorio especificado)
        model_file = self.save_model(model_output_dir)
        
        # 9. NUEVO: Registrar métricas para seguimiento
        self.log_training_metrics(metrics, validation_results, model_file)
        
        print("\n🏆 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        
        # Retornar métricas junto con información de validación
        return {
            **metrics,
            'validation_status': validation_results['performance_status'],
            'warnings_count': len(validation_results['warnings']),
            'model_file': model_file
        }
    
    def save_model(self, model_path: str = "models/", use_s3: bool = True) -> str:
        """
        Guarda el modelo entrenado localmente y/o en S3
        
        Args:
            model_path: Directorio local para guardar (usado como backup)
            use_s3: Si True, sube el modelo a S3
        
        Returns:
            str: Path del modelo (S3 key si use_s3=True, local path si use_s3=False)
        """
        if not self.is_trained:
            raise ValueError("El modelo debe ser entrenado antes de guardarlo")
        
        # Preparar datos del modelo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_data = {
            'model': self.model,
            'optimal_threshold': self.optimal_threshold,
            'cat_features_indices': self.cat_features_indices,
            'feature_names': self.feature_names,
            'random_state': self.random_state,
            'is_trained': self.is_trained,
            'timestamp': timestamp,
            'model_version': '1.0',
            'model_type': 'catboost_classifier'
        }
        
        # Guardar en S3 si está disponible
        if use_s3 and s3_model_manager is not None:
            try:
                model_name = f"uber_driver_model_{timestamp}.joblib"
                s3_key = s3_model_manager.upload_model(model_data, model_name)
                print(f"💾 Modelo guardado en S3: s3://{s3_model_manager.bucket_name}/{s3_key}")
                
                # También guardar copia local como backup
                os.makedirs(model_path, exist_ok=True)
                local_file = os.path.join(model_path, model_name)
                joblib.dump(model_data, local_file)
                print(f"💾 Copia local guardada en: {local_file}")
                
                return s3_key
                
            except Exception as e:
                print(f"⚠️  Error guardando en S3: {e}")
                print("💾 Guardando solo localmente como respaldo...")
        
        # Guardar solo localmente
        os.makedirs(model_path, exist_ok=True)
        model_file = os.path.join(model_path, f"uber_driver_model_{timestamp}.joblib")
        
        joblib.dump(model_data, model_file)
        print(f"💾 Modelo guardado localmente en: {model_file}")
        
        return model_file
    
    def load_model(self, model_file: str) -> None:
        """
        Carga un modelo previamente entrenado
        """
        print(f"📂 Cargando modelo desde: {model_file}")
        
        model_data = joblib.load(model_file)
        
        self.model = model_data['model']
        self.optimal_threshold = model_data['optimal_threshold']
        self.cat_features_indices = model_data['cat_features_indices']
        self.feature_names = model_data['feature_names']
        self.random_state = model_data['random_state']
        self.is_trained = model_data['is_trained']
        
        print("   ✅ Modelo cargado exitosamente")
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Obtiene la importancia de las features
        """
        if not self.is_trained:
            raise ValueError("El modelo debe ser entrenado primero")
        
        importance = self.model.get_feature_importance()
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return feature_importance.head(top_n)


def entrenar_modelo_desde_csv(csv_file: str, model_output_dir: str = "models/", use_safe_features_only: bool = True) -> str:
    """
    Función de conveniencia para entrenar el modelo desde un archivo CSV
    
    Args:
        csv_file: Path al archivo CSV
        model_output_dir: Directorio para guardar el modelo
        use_safe_features_only: Si True, usa solo features seguras sin riesgo de data leakage
    """
    print(f"🔒 MODO ENTRENAMIENTO: {'SEGURO (sin data leakage)' if use_safe_features_only else 'COMPLETO (con todas las features)'}")
    print(f"📁 Directorio de salida: {model_output_dir}")
    
    # Crear instancia del modelo
    model = UberDriverAvailabilityModel()
    
    # Entrenar pipeline completo (pasando el directorio de salida)
    metrics = model.train_complete_pipeline(csv_file, use_safe_features=use_safe_features_only, 
                                          model_output_dir=model_output_dir)
    
    # Mostrar importancia de features
    print("\n📈 TOP 15 FEATURES MÁS IMPORTANTES:")
    feature_importance = model.get_feature_importance(15)
    for idx, row in feature_importance.iterrows():
        print(f"   {row['feature']}: {row['importance']:.2f}")
    
    return metrics['model_file']


def entrenar_modelo_seguro_desde_csv(csv_file: str, model_output_dir: str = "models/") -> str:
    """
    Función específica para entrenar con features seguras únicamente
    """
    return entrenar_modelo_desde_csv(csv_file, model_output_dir, use_safe_features_only=True)


if __name__ == "__main__":
    # Ejemplo de uso
    csv_file = "../data/ncr_ride_bookings.csv"
    
    if os.path.exists(csv_file):
        print("🔒 ENTRENANDO CON FEATURES SEGURAS (sin data leakage)")
        model_file = entrenar_modelo_seguro_desde_csv(csv_file)
        print(f"\n🎉 Modelo entrenado y guardado en: {model_file}")
        
        print("\n" + "="*60)
        print("💡 Para entrenar con todas las features (con riesgo de leakage):")
        print("   entrenar_modelo_desde_csv(csv_file, use_safe_features_only=False)")
    else:
        print(f"❌ Archivo no encontrado: {csv_file}")
        print("   Ejecutar desde el directorio correcto o proporcionar la ruta correcta")
