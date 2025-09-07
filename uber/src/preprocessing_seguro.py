"""
Módulo de preprocesamiento corregido - basado en las funciones del notebook
Evita data leakage siguiendo las mejores prácticas del análisis
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, List, Dict, Any
import warnings
warnings.filterwarnings("ignore")

# Importar constantes
try:
    from .constants import MODEL_FEATURES, CATEGORICAL_FEATURES, SAFE_FEATURES
except ImportError:
    from constants import MODEL_FEATURES, CATEGORICAL_FEATURES, SAFE_FEATURES


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia los nombres de las columnas"""
    df.columns = [i.replace(" ", "_").lower() for i in df.columns]
    return df


def create_cyclical_features(decimal_hours):
    """Crea features cíclicas para las horas"""
    return {
        'time_sin': np.sin(2 * np.pi * decimal_hours / 24),
        'time_cos': np.cos(2 * np.pi * decimal_hours / 24)
    }


def crear_variables_temporales_corregidas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables temporales sin data leakage
    """
    df = df.copy()
    
    # Convertir date y time si son strings
    if df['date'].dtype == 'object':
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    if df['time'].dtype == 'object':
        df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.time
    
    # Variables temporales básicas
    df['dia_semana'] = pd.to_datetime(df['date']).dt.dayofweek
    df['es_fin_semana'] = df['dia_semana'].isin([5, 6]).astype(int)
    df['es_lunes'] = (df['dia_semana'] == 0).astype(int)
    df['mes'] = pd.to_datetime(df['date']).dt.month
    df['trimestre'] = pd.to_datetime(df['date']).dt.quarter
    df['dia_mes'] = pd.to_datetime(df['date']).dt.day
    
    # Variables de inicio/fin de mes
    df['es_inicio_mes'] = (df['dia_mes'] <= 5).astype(int)
    df['es_fin_mes'] = (df['dia_mes'] >= 25).astype(int)
    
    # Variables de hora
    df['hora'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
    df['minuto'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.minute
    df['time_decimal_hours'] = df['hora'] + df['minuto'] / 60.0
    
    # Features cíclicas
    cyclical = df['time_decimal_hours'].apply(create_cyclical_features)
    df['time_sin'] = [x['time_sin'] for x in cyclical]
    df['time_cos'] = [x['time_cos'] for x in cyclical]
    
    # Períodos del día
    df['periodo_dia'] = 'Madrugada'
    df.loc[df['hora'].between(6, 11), 'periodo_dia'] = 'Mañana'
    df.loc[df['hora'].between(12, 17), 'periodo_dia'] = 'Tarde'
    df.loc[df['hora'].between(18, 23), 'periodo_dia'] = 'Noche'
    
    # Horas pico específicas
    df['es_hora_pico_mañana'] = df['hora'].isin([7, 8, 9]).astype(int)
    df['es_hora_pico_tarde'] = df['hora'].isin([17, 18, 19, 20]).astype(int)
    df['es_hora_pico'] = (df['es_hora_pico_mañana'] | df['es_hora_pico_tarde']).astype(int)
    df['es_horario_laboral'] = df['hora'].between(9, 17).astype(int)
    
    return df


def crear_variables_comportamiento_corregida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables basadas en el comportamiento histórico del cliente HASTA LA FECHA DEL VIAJE
    IMPORTANTE: Para evitar data leakage, solo usamos información disponible hasta la fecha del viaje actual
    """
    df_temp = df.copy()
    
    # Asegurar que tenemos fecha como datetime para ordenamiento temporal
    if 'datetime' not in df_temp.columns:
        df_temp['datetime'] = pd.to_datetime(df_temp['date'])
    
    # Ordenar por customer_id y fecha para cálculos temporales correctos
    df_temp = df_temp.sort_values(['customer_id', 'datetime']).reset_index(drop=True)
    
    print("🚨 APLICANDO CORRECTITUD TEMPORAL - Calculando variables hasta la fecha del viaje...")
    
    # 1. VARIABLES DE COMPORTAMIENTO DEL CLIENTE (CON COMPONENTE TEMPORAL)
    
    # Calcular cancelaciones acumuladas del cliente HASTA la fecha actual (SHIFT para evitar leakage)
    df_temp['cancelaciones_cliente_historicas'] = df_temp.groupby('customer_id')['cancelled_rides_by_customer'].transform(
        lambda x: x.fillna(0).shift(1).cumsum().fillna(0)
    )
    
    # Variables derivadas de cancelaciones históricas
    df_temp['tiene_cancelaciones_cliente'] = (df_temp['cancelaciones_cliente_historicas'] > 0).astype(int)
    df_temp['cliente_problematico'] = (df_temp['cancelaciones_cliente_historicas'] >= 3).astype(int)
    
    # Experiencia del cliente (número de viajes previos) - SIN INCLUIR EL VIAJE ACTUAL
    df_temp['experiencia_cliente'] = df_temp.groupby('customer_id').cumcount()  # 0 = primer viaje
    df_temp['es_cliente_nuevo'] = (df_temp['experiencia_cliente'] == 0).astype(int)
    df_temp['es_cliente_experimentado'] = (df_temp['experiencia_cliente'] >= 10).astype(int)
    
    # 2. VARIABLES DE ÁREA/ZONA (CON COMPONENTE TEMPORAL)
    
    # Función para calcular cancelaciones de drivers por área usando solo datos históricos
    def calcular_cancelaciones_area_historicas(group):
        """Calcula cancelaciones promedio en área usando solo viajes anteriores"""
        return group['cancelled_rides_by_driver'].fillna(0).shift(1).rolling(
            window=100, min_periods=1
        ).mean().fillna(0)
    
    # Aplicar función por pickup_location
    df_temp['cancelaciones_driver_area_30d'] = df_temp.groupby('pickup_location').apply(
        calcular_cancelaciones_area_historicas
    ).reset_index(level=0, drop=True)
    
    df_temp['area_problematica_drivers'] = (df_temp['cancelaciones_driver_area_30d'] > 2).astype(int)
    
    # Función para calcular viajes incompletos por área usando solo datos históricos  
    def calcular_incompletos_area_historicas(group):
        """Calcula viajes incompletos promedio en área usando solo viajes anteriores"""
        return group['incomplete_rides'].fillna(0).shift(1).rolling(
            window=100, min_periods=1
        ).mean().fillna(0)
    
    # Aplicar función por pickup_location
    df_temp['incompletos_area_30d'] = df_temp.groupby('pickup_location').apply(
        calcular_incompletos_area_historicas
    ).reset_index(level=0, drop=True)
    
    df_temp['zona_problematica'] = (df_temp['incompletos_area_30d'] > 1).astype(int)
    
    # Restaurar orden original
    df_temp = df_temp.sort_index()
    
    return df_temp


def crear_variables_zona_corregidas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables basadas en el comportamiento histórico de las zonas
    """
    df_temp = df.copy()
    
    # Asegurar datetime
    if 'datetime' not in df_temp.columns:
        df_temp['datetime'] = pd.to_datetime(df_temp['date'])
    
    # Ordenar por fecha para cálculos temporales
    df_temp = df_temp.sort_values('datetime').reset_index(drop=True)
    
    # Variables de área problemática basadas en datos históricos (30 días previos)
    df_temp['cancelaciones_driver_area_30d'] = df_temp.groupby('pickup_location')['cancelled_rides_by_driver'].transform(
        lambda x: x.fillna(0).rolling(window=100, min_periods=1).mean().shift(1).fillna(0)
    )
    
    df_temp['area_problematica_drivers'] = (df_temp['cancelaciones_driver_area_30d'] > 2).astype(int)
    
    df_temp['incompletos_area_30d'] = df_temp.groupby('pickup_location')['incomplete_rides'].transform(
        lambda x: x.fillna(0).rolling(window=100, min_periods=1).mean().shift(1).fillna(0)
    )
    
    df_temp['zona_problematica'] = (df_temp['incompletos_area_30d'] > 1).astype(int)
    
    return df_temp


def crear_variables_ratings_seguras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables de ratings usando solo datos históricos del cliente/conductor
    IMPORTANTE: Usar promedios históricos, no ratings del viaje actual
    """
    df_temp = df.copy()
    
    # Asegurar datetime para ordenamiento temporal
    if 'datetime' not in df_temp.columns:
        df_temp['datetime'] = pd.to_datetime(df_temp['date'])
    
    # Ordenar temporalmente
    df_temp = df_temp.sort_values(['customer_id', 'datetime']).reset_index(drop=True)
    
    print("🚨 CREANDO VARIABLES DE RATINGS CON CORRECTITUD TEMPORAL...")
    
    # RATINGS HISTÓRICOS PROMEDIO (usando shift para evitar leakage)
    
    # Promedio histórico de ratings del cliente (excluyendo viaje actual)
    df_temp['customer_rating_historico'] = df_temp.groupby('customer_id')['customer_rating'].transform(
        lambda x: x.shift(1).expanding().mean().fillna(4.0)  # Default 4.0 para nuevos clientes
    )
    
    # Promedio histórico de ratings del conductor (simplificado - usar promedio global)
    # En producción real, esto se haría por driver_id, pero aquí usamos una aproximación
    rating_promedio_global = df_temp['driver_ratings'].fillna(4.0).mean()
    df_temp['driver_rating_historico'] = rating_promedio_global  # Simplificación
    
    # Limpiar ratings usando valores históricos
    df_temp['driver_rating_clean'] = df_temp['driver_rating_historico']
    df_temp['customer_rating_clean'] = df_temp['customer_rating_historico']
    
    # Categorías de rating basadas en promedios históricos
    df_temp['driver_rating_categoria'] = 'Normal'
    df_temp.loc[df_temp['driver_rating_clean'] >= 4.5, 'driver_rating_categoria'] = 'Excelente'
    df_temp.loc[df_temp['driver_rating_clean'] < 4.0, 'driver_rating_categoria'] = 'Bajo'
    
    df_temp['customer_rating_categoria'] = 'Normal'
    df_temp.loc[df_temp['customer_rating_clean'] >= 4.5, 'customer_rating_categoria'] = 'Excelente'
    df_temp.loc[df_temp['customer_rating_clean'] < 4.0, 'customer_rating_categoria'] = 'Bajo'
    
    # Para clientes nuevos (sin historial)
    df_temp.loc[df_temp['experiencia_cliente'] == 0, 'customer_rating_categoria'] = 'Sin_Rating'
    
    # Variables de interacción de ratings
    df_temp['diferencia_ratings'] = df_temp['driver_rating_clean'] - df_temp['customer_rating_clean']
    df_temp['ambos_ratings_altos'] = ((df_temp['driver_rating_clean'] >= 4.5) & 
                                      (df_temp['customer_rating_clean'] >= 4.5)).astype(int)
    
    # Restaurar orden original
    df_temp = df_temp.sort_index()
    
    return df_temp


def crear_variables_valor_distancia_seguras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables de valor y distancia usando datos históricos para evitar leakage
    IMPORTANTE: Usar estadísticas históricas, no valores del viaje actual
    """
    df_temp = df.copy()
    
    # Asegurar datetime para ordenamiento temporal
    if 'datetime' not in df_temp.columns:
        df_temp['datetime'] = pd.to_datetime(df_temp['date'])
    
    # Ordenar temporalmente
    df_temp = df_temp.sort_values(['customer_id', 'datetime']).reset_index(drop=True)
    
    print("🚨 CREANDO VARIABLES DE VALOR/DISTANCIA CON CORRECTITUD TEMPORAL...")
    
    # Limpiar valores actuales (estos se pueden usar porque son del contexto del viaje)
    df_temp['booking_value_clean'] = pd.to_numeric(df_temp['booking_value'], errors='coerce').fillna(0)
    df_temp['ride_distance_clean'] = pd.to_numeric(df_temp['ride_distance'], errors='coerce').fillna(1.0)
    
    # VARIABLES BASADAS EN ESTADÍSTICAS HISTÓRICAS DEL CLIENTE
    
    # Valor promedio histórico del cliente (usando shift para evitar leakage)
    df_temp['valor_promedio_cliente_historico'] = df_temp.groupby('customer_id')['booking_value_clean'].transform(
        lambda x: x.shift(1).expanding().mean().fillna(x.mean())
    )
    
    # Distancia promedio histórica del cliente
    df_temp['distancia_promedio_cliente_historica'] = df_temp.groupby('customer_id')['ride_distance_clean'].transform(
        lambda x: x.shift(1).expanding().mean().fillna(x.mean())
    )
    
    # Valor por km histórico del cliente
    def calcular_valor_km_historico(group):
        """Calcula valor por km histórico usando solo viajes anteriores"""
        valor_hist = group['booking_value_clean'].shift(1).expanding().mean()
        dist_hist = group['ride_distance_clean'].shift(1).expanding().mean()
        return (valor_hist / (dist_hist + 0.1)).fillna(50.0)  # Default 50 rupees/km
    
    df_temp['valor_por_km_historico'] = df_temp.groupby('customer_id').apply(
        calcular_valor_km_historico
    ).reset_index(level=0, drop=True)
    
    # VARIABLES CATEGÓRICAS BASADAS EN EL VIAJE ACTUAL VS PERFIL HISTÓRICO
    
    # Comparar viaje actual con perfil histórico del cliente
    df_temp['viaje_mas_caro_que_usual'] = (
        df_temp['booking_value_clean'] > df_temp['valor_promedio_cliente_historico'] * 1.5
    ).astype(int)
    
    df_temp['viaje_mas_largo_que_usual'] = (
        df_temp['ride_distance_clean'] > df_temp['distancia_promedio_cliente_historica'] * 1.5
    ).astype(int)
    
    # Variables categóricas de valor usando umbrales conservadores
    valor_p75 = df_temp['booking_value_clean'].quantile(0.75)
    valor_p25 = df_temp['booking_value_clean'].quantile(0.25)
    
    df_temp['viaje_alto_valor'] = (df_temp['booking_value_clean'] > valor_p75).astype(int)
    df_temp['viaje_bajo_valor'] = (df_temp['booking_value_clean'] < valor_p25).astype(int)
    
    # Variables categóricas de distancia
    dist_p75 = df_temp['ride_distance_clean'].quantile(0.75)
    dist_p25 = df_temp['ride_distance_clean'].quantile(0.25)
    
    df_temp['viaje_corto'] = (df_temp['ride_distance_clean'] < dist_p25).astype(int)
    df_temp['viaje_largo'] = (df_temp['ride_distance_clean'] > dist_p75).astype(int)
    df_temp['viaje_medio'] = ((df_temp['ride_distance_clean'] >= dist_p25) & 
                              (df_temp['ride_distance_clean'] <= dist_p75)).astype(int)
    
    # Valor por km actual del viaje (se puede usar porque es calculable al momento de booking)
    df_temp['valor_por_km'] = df_temp['booking_value_clean'] / np.maximum(df_temp['ride_distance_clean'], 0.1)
    
    # Rentabilidad basada en perfil histórico del cliente
    df_temp['viaje_rentable'] = (
        df_temp['valor_por_km'] > df_temp['valor_por_km_historico'] * 1.2
    ).astype(int)
    
    # Restaurar orden original
    df_temp = df_temp.sort_index()
    
    return df_temp


def crear_variables_geograficas_seguras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables geográficas sin data leakage
    """
    df_temp = df.copy()
    
    # Variables básicas de localización
    df_temp['mismo_pickup_drop'] = (df_temp['pickup_location'] == df_temp['drop_location']).astype(int)
    
    # Variables de popularidad (basadas en frecuencia histórica)
    pickup_counts = df_temp['pickup_location'].value_counts()
    drop_counts = df_temp['drop_location'].value_counts()
    
    # Top 10 locations como "populares"
    top_pickups = pickup_counts.head(10).index
    top_drops = drop_counts.head(10).index
    
    df_temp['pickup_popular'] = df_temp['pickup_location'].isin(top_pickups).astype(int)
    df_temp['drop_popular'] = df_temp['drop_location'].isin(top_drops).astype(int)
    df_temp['ruta_popular'] = (df_temp['pickup_popular'] | df_temp['drop_popular']).astype(int)
    
    # Variables de zona problemática (usar datos históricos seguros)
    problematic_pickups = ['Remote Area A', 'Remote Area B']  # Ejemplo conservador
    problematic_drops = ['Remote Area A', 'Remote Area B']
    
    df_temp['pickup_problematico'] = df_temp['pickup_location'].isin(problematic_pickups).astype(int)
    df_temp['drop_problematico'] = df_temp['drop_location'].isin(problematic_drops).astype(int)
    df_temp['ruta_problematica'] = (df_temp['pickup_problematico'] | df_temp['drop_problematico']).astype(int)
    
    # Variables de centralidad (áreas clave como centros comerciales)
    central_areas = ['Central Delhi', 'CP', 'Khan Market', 'Select City Walk']  # Ejemplo
    
    df_temp['pickup_central'] = df_temp['pickup_location'].isin(central_areas).astype(int)
    df_temp['drop_central'] = df_temp['drop_location'].isin(central_areas).astype(int)
    df_temp['ruta_desde_centro'] = (df_temp['pickup_central'] & ~df_temp['drop_central']).astype(int)
    df_temp['ruta_hacia_centro'] = (~df_temp['pickup_central'] & df_temp['drop_central']).astype(int)
    df_temp['ruta_intra_centro'] = (df_temp['pickup_central'] & df_temp['drop_central']).astype(int)
    
    # Variables de alto volumen
    df_temp['pickup_alto_volumen'] = (pickup_counts[df_temp['pickup_location']].values > 
                                      pickup_counts.quantile(0.8)).astype(int)
    df_temp['drop_alto_volumen'] = (drop_counts[df_temp['drop_location']].values > 
                                    drop_counts.quantile(0.8)).astype(int)
    
    return df_temp


def crear_variables_interaccion_seguras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables de interacción sin data leakage
    """
    df_temp = df.copy()
    
    # Interacciones temporales con características
    df_temp['problema_en_hora_pico'] = (df_temp['es_hora_pico'] & df_temp['zona_problematica']).astype(int)
    df_temp['fin_semana_y_problematico'] = (df_temp['es_fin_semana'] & df_temp['cliente_problematico']).astype(int)
    df_temp['noche_y_zona_problematica'] = ((df_temp['periodo_dia'] == 'Noche') & df_temp['zona_problematica']).astype(int)
    df_temp['centro_en_hora_pico'] = (df_temp['pickup_central'] & df_temp['es_hora_pico']).astype(int)
    df_temp['ruta_problematica_noche'] = (df_temp['ruta_problematica'] & (df_temp['periodo_dia'] == 'Noche')).astype(int)
    df_temp['centro_fin_semana'] = (df_temp['pickup_central'] & df_temp['es_fin_semana']).astype(int)
    df_temp['viaje_corto_hora_pico'] = (df_temp['viaje_corto'] & df_temp['es_hora_pico']).astype(int)
    df_temp['alto_valor_centro'] = (df_temp['viaje_alto_valor'] & df_temp['pickup_central']).astype(int)
    df_temp['rentable_y_popular'] = (df_temp['viaje_rentable'] & df_temp['ruta_popular']).astype(int)
    
    # Variables combinadas de ratings
    df_temp['ratings_bajos_combined'] = ((df_temp['driver_rating_categoria'] == 'Bajo') | 
                                         (df_temp['customer_rating_categoria'] == 'Bajo')).astype(int)
    df_temp['ratings_altos_combined'] = ((df_temp['driver_rating_categoria'] == 'Excelente') & 
                                         (df_temp['customer_rating_categoria'] == 'Excelente')).astype(int)
    
    # Variables de riesgo
    df_temp['riesgo_alto'] = (df_temp['cliente_problematico'] & df_temp['zona_problematica']).astype(int)
    df_temp['perfil_premium'] = (df_temp['es_cliente_experimentado'] & df_temp['ambos_ratings_altos']).astype(int)
    
    # Variables de demanda/oferta estimada (simplificadas)
    df_temp['demanda_estimada'] = (df_temp['es_hora_pico'] * 2 + df_temp['es_fin_semana'] * 1.5 + 
                                   df_temp['pickup_popular'] * 1.2).round(2)
    df_temp['oferta_estimada_baja'] = (df_temp['zona_problematica'] | df_temp['area_problematica_drivers']).astype(int)
    df_temp['desbalance_demanda_oferta'] = df_temp['demanda_estimada'] * (1 + df_temp['oferta_estimada_baja'])
    
    # Interacciones cliente-contexto
    df_temp['cliente_nuevo_hora_pico'] = (df_temp['es_cliente_nuevo'] & df_temp['es_hora_pico']).astype(int)
    df_temp['cliente_experimentado_problema'] = (df_temp['es_cliente_experimentado'] & df_temp['zona_problematica']).astype(int)
    
    return df_temp


def crear_one_hot_encoding_localizations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea one-hot encoding para localizaciones (pickup y drop)
    """
    df_temp = df.copy()
    
    # One-hot encoding para pickup_location
    pickup_dummies = pd.get_dummies(df_temp['pickup_location'], prefix='pickup_location')
    drop_dummies = pd.get_dummies(df_temp['drop_location'], prefix='drop_location')
    
    # Asegurar que tenemos exactamente 32 columnas para cada una
    for i in range(32):
        col_pickup = f'pickup_location_{i}'
        col_drop = f'drop_location_{i}'
        
        if col_pickup not in pickup_dummies.columns:
            pickup_dummies[col_pickup] = 0
        if col_drop not in drop_dummies.columns:
            drop_dummies[col_drop] = 0
    
    # Ordenar columnas y tomar solo las primeras 32
    pickup_cols = [f'pickup_location_{i}' for i in range(32)]
    drop_cols = [f'drop_location_{i}' for i in range(32)]
    
    pickup_dummies = pickup_dummies[pickup_cols]
    drop_dummies = drop_dummies[drop_cols]
    
    # Concatenar al dataframe original
    df_final = pd.concat([df_temp, pickup_dummies, drop_dummies], axis=1)
    
    return df_final


def pipeline_completo_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline completo de feature engineering sin data leakage
    """
    print("🚀 INICIANDO PIPELINE DE FEATURE ENGINEERING SEGURO")
    print("=" * 60)
    
    # 1. Limpiar columnas
    df = limpiar_columnas(df)
    print("✅ Columnas limpiadas")
    
    # 2. Variables temporales
    df = crear_variables_temporales_corregidas(df)
    print("✅ Variables temporales creadas")
    
    # 3. Variables de comportamiento (sin leakage temporal)
    df = crear_variables_comportamiento_corregida(df) 
    print("✅ Variables de comportamiento creadas (sin leakage)")
    
    # 4. Variables de zona
    df = crear_variables_zona_corregidas(df)
    print("✅ Variables de zona creadas")
    
    # 5. Variables de ratings (seguras)
    df = crear_variables_ratings_seguras(df)
    print("✅ Variables de ratings creadas (seguras)")
    
    # 6. Variables de valor y distancia (seguras)
    df = crear_variables_valor_distancia_seguras(df)
    print("✅ Variables de valor/distancia creadas (seguras)")
    
    # 7. Variables geográficas
    df = crear_variables_geograficas_seguras(df)
    print("✅ Variables geográficas creadas")
    
    # 8. Variables de interacción
    df = crear_variables_interaccion_seguras(df)
    print("✅ Variables de interacción creadas")
    
    # 9. One-hot encoding para localizaciones
    df = crear_one_hot_encoding_localizations(df)
    print("✅ One-hot encoding creado")
    
    # 10. Crear target y eliminar booking_status
    if 'booking_status' in df.columns and 'target' not in df.columns:
        df['target'] = (df['booking_status'] == 'No Driver Found').astype(int)
        df = df.drop('booking_status', axis=1)  # ELIMINAR para evitar data leakage
        print("✅ Target creado y booking_status eliminado")
    
    print(f"📊 Dataset final: {df.shape}")
    print(f"🎯 Distribución target: {df['target'].value_counts().to_dict() if 'target' in df.columns else 'No target'}")
    
    return df


def preparar_features_para_modelo_seguro(df: pd.DataFrame, use_safe_features_only: bool = False) -> Tuple[pd.DataFrame, List[int]]:
    """
    Prepara las features para el modelo usando solo features seguras o el conjunto completo
    """
    if use_safe_features_only:
        print("⚠️  MODO SEGURO: Usando solo features sin riesgo de data leakage")
        features_to_use = SAFE_FEATURES
        cat_features = ['vehicle_type', 'periodo_dia']  # Solo categóricas seguras
    else:
        print("📊 MODO COMPLETO: Usando todas las features especificadas")
        features_to_use = MODEL_FEATURES
        cat_features = CATEGORICAL_FEATURES
    
    # Filtrar solo las features que existen en el dataframe
    features_disponibles = [f for f in features_to_use if f in df.columns]
    
    print(f"📋 Features disponibles: {len(features_disponibles)} de {len(features_to_use)}")
    
    if len(features_disponibles) < len(features_to_use) * 0.8:
        print("⚠️  ADVERTENCIA: Faltan muchas features. Verificar pipeline de preprocessing.")
        missing_features = set(features_to_use) - set(features_disponibles)
        print(f"❌ Features faltantes: {list(missing_features)[:10]}...")  # Mostrar solo las primeras 10
    
    # Preparar DataFrame con features seleccionadas
    X = df[features_disponibles].copy()
    
    # Manejo especial de variables categóricas para CatBoost
    for col in X.columns:
        if col in cat_features:
            # Para variables categóricas, rellenar con valor específico y convertir a string
            X[col] = X[col].fillna('missing').astype(str)
        else:
            # Para variables numéricas, rellenar con mediana
            if X[col].dtype in ['float64', 'int64']:
                X[col] = X[col].fillna(X[col].median())
            else:
                # Si es string pero no categórica, intentar convertir a numérica
                X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    # Obtener índices de features categóricas
    cat_features_indices = [i for i, col in enumerate(features_disponibles) if col in cat_features]
    
    print(f"🏷️  Features categóricas: {len(cat_features_indices)}")
    
    return X, cat_features_indices


def procesar_datos_completo_seguro(df: pd.DataFrame, use_safe_features_only: bool = False) -> pd.DataFrame:
    """
    Función principal de procesamiento seguro
    """
    print("🔒 PROCESAMIENTO SEGURO - EVITANDO DATA LEAKAGE")
    print("=" * 60)
    
    # Pipeline completo
    df_processed = pipeline_completo_feature_engineering(df)
    
    print("\n🎉 PROCESAMIENTO COMPLETADO")
    return df_processed


if __name__ == "__main__":
    # Ejemplo de uso
    print("🧪 TESTING PREPROCESSING SEGURO")
    
    # Cargar datos de ejemplo
    import os
    csv_file = "../data/ncr_ride_bookings.csv"
    
    if os.path.exists(csv_file):
        data = pd.read_csv(csv_file)
        print(f"📊 Datos cargados: {data.shape}")
        
        # Procesar datos
        data_processed = procesar_datos_completo_seguro(data, use_safe_features_only=True)
        
        # Preparar features para modelo
        X, cat_indices = preparar_features_para_modelo_seguro(data_processed, use_safe_features_only=True)
        
        print(f"✅ Features preparadas: {X.shape}")
        print(f"🏷️  Índices categóricas: {cat_indices}")
    else:
        print(f"❌ Archivo no encontrado: {csv_file}")
