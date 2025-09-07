"""
Constantes y configuraciones para el modelo de predicción de disponibilidad de conductores
"""

# Variables para el modelo (sin data leakage)
MODEL_FEATURES = [
    # Variables de localización (one-hot encoded)
    f"pickup_location_{i}" for i in range(32)
] + [
    f"drop_location_{i}" for i in range(32)
] + [
    # Variables básicas del viaje
    "vehicle_type",
    
    # Variables temporales
    "time_decimal_hours",
    "time_sin",
    "time_cos",
    'dia_semana',
    'es_fin_semana',
    'es_lunes',
    'mes',
    'trimestre',
    'dia_mes',
    'es_inicio_mes',
    'es_fin_mes',
    'hora',
    'periodo_dia',
    'es_hora_pico_mañana',
    'es_hora_pico_tarde',
    'es_hora_pico',
    'es_horario_laboral',
    
    # Variables históricas del cliente (SIN LEAKAGE)
    'cancelaciones_cliente_historicas',
    'tiene_cancelaciones_cliente',
    'cliente_problematico',
    'experiencia_cliente',
    'es_cliente_nuevo',
    'es_cliente_experimentado',
    
    # Variables del área/zona (históricas)
    'cancelaciones_driver_area_30d',
    'area_problematica_drivers',
    'incompletos_area_30d',
    'zona_problematica',
    
    # Variables de ratings (CUIDADO: estas pueden tener leakage)
    #'driver_rating_clean',
    #'customer_rating_clean',
    #'driver_rating_categoria',
    #'customer_rating_categoria',
    #'diferencia_ratings',
    #'ambos_ratings_altos',
    
    # Variables de valor y distancia (CUIDADO: estas pueden tener leakage)
    #'booking_value_clean',
    #'viaje_alto_valor',
    #'viaje_bajo_valor',
    #'ride_distance_clean',
    #'viaje_corto',
    #'viaje_largo',
    #'viaje_medio',
    #'valor_por_km',
    #'viaje_rentable',
    'valor_promedio_cliente_historico',
    #'viaje_mas_caro_que_usual',
    
    # Variables geográficas
    'mismo_pickup_drop',
    'pickup_popular',
    'drop_popular',
    'ruta_popular',
    'pickup_problematico',
    'drop_problematico',
    'ruta_problematica',
    'pickup_central',
    'drop_central',
    'ruta_desde_centro',
    'ruta_hacia_centro',
    'ruta_intra_centro',
    'pickup_alto_volumen',
    'drop_alto_volumen',
    
    # Variables de interacción
    'problema_en_hora_pico',
    'fin_semana_y_problematico',
    'noche_y_zona_problematica',
    'centro_en_hora_pico',
    'ruta_problematica_noche',
    'centro_fin_semana',
    #'viaje_corto_hora_pico',
    #'alto_valor_centro',
    #'rentable_y_popular',
    #'ratings_bajos_combined',
    #'ratings_altos_combined',
    #'riesgo_alto',
    #'perfil_premium',
    
    # Variables de demanda/oferta
    'demanda_estimada',
    'oferta_estimada_baja',
    'desbalance_demanda_oferta',
    'cliente_nuevo_hora_pico',
    'cliente_experimentado_problema'
]

# Variables categóricas para CatBoost (solo las que están en MODEL_FEATURES)
CATEGORICAL_FEATURES = [
    'vehicle_type',
    'periodo_dia'
]

# Variables que pueden tener data leakage - USAR CON CUIDADO
POTENTIAL_LEAKAGE_FEATURES = [
    'driver_rating_clean',
    'customer_rating_clean', 
    'driver_rating_categoria',
    'customer_rating_categoria',
    'booking_value_clean',
    'ride_distance_clean',
    'valor_por_km',
    'viaje_rentable'
]

# Features básicas sin riesgo de leakage
SAFE_FEATURES = [
    'vehicle_type',
    'time_decimal_hours',
    'time_sin', 
    'time_cos',
    'dia_semana',
    'es_fin_semana',
    'es_lunes',
    'mes',
    'trimestre',
    'dia_mes',
    'es_inicio_mes',
    'es_fin_mes',
    'hora',
    'periodo_dia',
    'es_hora_pico_mañana',
    'es_hora_pico_tarde', 
    'es_hora_pico',
    'es_horario_laboral',
    'pickup_central',
    'drop_central',
    'mismo_pickup_drop',
    'pickup_popular',
    'drop_popular',
    'ruta_popular'
]

# Configuración del modelo
MODEL_CONFIG = {
    'random_state': 42,
    'test_size': 0.2,
    'catboost_params': {
        'iterations': 1000,
        'learning_rate': 0.1,
        'depth': 6,
        'eval_metric': 'F1',
        'verbose': False
    },
    'resampling': 'RandomUnderSampler'
}

# Umbrales para validación de modelo
VALIDATION_THRESHOLDS = {
    'f1_score': 0.75,
    'precision': 0.75,
    'recall': 0.70,
    'roc_auc': 0.85,
    'accuracy': 0.80
}

VALIDATION_TOLERANCE = {
    'f1_score': 0.05,
    'precision': 0.05,
    'recall': 0.05,
    'roc_auc': 0.03,
    'accuracy': 0.05
}
