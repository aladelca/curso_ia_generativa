"""
Módulo de preprocesamiento y feature engineering
"""
import pandas as pd
import numpy as np
from datetime import datetime, date, time
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings("ignore")


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia los nombres de las columnas"""
    df.columns = [i.replace(" ", "_").lower() for i in df.columns]
    return df


def crear_variables_temporales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables temporales basadas en fecha y hora
    """
    df = df.copy()
    
    # Convertir date y time si son strings
    if df['date'].dtype == 'object':
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    if df['time'].dtype == 'object':
        df["time"] = pd.to_datetime(df["time"], errors="coerce").dt.time
    
    # Variables temporales
    df['dia_semana'] = pd.to_datetime(df['date']).dt.dayofweek
    df['es_fin_semana'] = df['dia_semana'].isin([5, 6]).astype(int)
    df['mes'] = pd.to_datetime(df['date']).dt.month
    df['dia_mes'] = pd.to_datetime(df['date']).dt.day
    
    # Variables de hora
    df['hora'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
    df['minuto'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.minute
    
    # Períodos del día
    df['periodo_dia'] = 'Madrugada'
    df.loc[df['hora'].between(6, 11), 'periodo_dia'] = 'Mañana'
    df.loc[df['hora'].between(12, 17), 'periodo_dia'] = 'Tarde'
    df.loc[df['hora'].between(18, 23), 'periodo_dia'] = 'Noche'
    
    # Horas pico
    df['es_hora_pico'] = df['hora'].isin([7, 8, 9, 17, 18, 19, 20]).astype(int)
    
    # Variables cíclicas
    df['hora_sin'] = np.sin(2 * np.pi * df['hora'] / 24)
    df['hora_cos'] = np.cos(2 * np.pi * df['hora'] / 24)
    df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)
    df['dia_semana_cos'] = np.cos(2 * np.pi * df['dia_semana'] / 7)
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    
    return df


def crear_variables_comportamiento_simplificada(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables de comportamiento del cliente de forma simplificada
    para evitar data leakage en tiempo real
    """
    df = df.copy()
    
    # Variables básicas de comportamiento (usando promedios globales como proxy)
    # En producción, estas se calcularían desde una base de datos histórica
    
    # Clientes problemáticos (usando un umbral basado en el dataset)
    df['es_cliente_nuevo'] = 0  # Por defecto, asumimos que no es nuevo
    df['cliente_problematico'] = 0  # Por defecto, no problemático
    
    # Variables de rating categorizadas
    df['driver_rating_categoria'] = 'Normal'
    df.loc[df['driver_ratings'] >= 4.5, 'driver_rating_categoria'] = 'Excelente'
    df.loc[df['driver_ratings'] < 4.0, 'driver_rating_categoria'] = 'Bajo'
    df.loc[df['driver_ratings'].isna(), 'driver_rating_categoria'] = 'Sin_Rating'
    
    df['customer_rating_categoria'] = 'Normal'
    df.loc[df['customer_rating'] >= 4.5, 'customer_rating_categoria'] = 'Excelente'
    df.loc[df['customer_rating'] < 4.0, 'customer_rating_categoria'] = 'Bajo'
    df.loc[df['customer_rating'].isna(), 'customer_rating_categoria'] = 'Sin_Rating'
    
    return df


def crear_variables_geograficas_simplificada(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables geográficas simplificadas basadas en locaciones
    """
    df = df.copy()
    
    # Áreas centrales más comunes (basado en el dataset)
    areas_centrales = [
        'Khan Market', 'Central Secretariat', 'CP', 'Cyber Hub', 
        'Gurgaon Sector 29', 'Noida Sector 18', 'Dwarka'
    ]
    
    # Variables de ubicación
    df['pickup_central'] = df['pickup_location'].isin(areas_centrales).astype(int)
    df['drop_central'] = df['drop_location'].isin(areas_centrales).astype(int)
    
    # Rutas populares (simplificado)
    df['es_ruta_popular'] = ((df['pickup_central'] == 1) | (df['drop_central'] == 1)).astype(int)
    
    # Variables de problemas por área (usando promedios estadísticos)
    # En producción, estos se calcularían desde datos históricos
    df['pickup_problematico'] = 0  # Por defecto
    df['area_problematica_drivers'] = 0  # Por defecto
    
    return df


def crear_variables_interaccion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables de interacción entre diferentes factores
    """
    df = df.copy()
    
    # Interacciones temporales y geográficas
    df['centro_en_hora_pico'] = df['pickup_central'] * df['es_hora_pico']
    df['problematico_fin_semana'] = df['cliente_problematico'] * df['es_fin_semana']
    df['problema_en_hora_pico'] = df['cliente_problematico'] * df['es_hora_pico']
    
    # Proxy de desbalance demanda-oferta
    df['desbalance_demanda_oferta'] = (
        df['es_hora_pico'] * df['pickup_central'] * df['es_fin_semana']
    )
    
    return df


def procesar_datos_completo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline completo de procesamiento de datos
    """
    df = df.copy()
    
    # Limpiar columnas
    df = limpiar_columnas(df)
    
    # Crear variables temporales
    df = crear_variables_temporales(df)
    
    # Crear variables de comportamiento
    df = crear_variables_comportamiento_simplificada(df)
    
    # Crear variables geográficas
    df = crear_variables_geograficas_simplificada(df)
    
    # Crear variables de interacción
    df = crear_variables_interaccion(df)
    
    # Crear target si no existe (para datos de entrenamiento)
    if 'booking_status' in df.columns and 'target' not in df.columns:
        df['target'] = (df['booking_status'] == 'No Driver Found').astype(int)
        # ELIMINAR booking_status para evitar data leakage
        df = df.drop('booking_status', axis=1)
    
    return df


def preparar_features_para_modelo(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepara las features para el modelo, seleccionando solo las más importantes
    """
    # Features categóricas para CatBoost
    cat_features = [
        'vehicle_type', 'periodo_dia', 'pickup_location', 'drop_location'
    ]
    
    # Features numéricas importantes
    numeric_features = [
        'hora', 'dia_semana', 'es_fin_semana', 'es_hora_pico',
        'pickup_central', 'drop_central', 'es_ruta_popular',
        'centro_en_hora_pico', 'desbalance_demanda_oferta',
        'hora_sin', 'hora_cos', 'dia_semana_sin', 'dia_semana_cos',
        'mes_sin', 'mes_cos', 'avg_vtat', 'avg_ctat', 'ride_distance'
    ]
    
    # Todas las features para el modelo
    features_modelo = cat_features + numeric_features
    
    # Filtrar solo las features que existen en el dataframe
    features_disponibles = [f for f in features_modelo if f in df.columns]
    
    # Preparar DataFrame con features seleccionadas
    X = df[features_disponibles].copy()
    
    # Rellenar valores nulos
    for col in X.columns:
        if X[col].dtype in ['float64', 'int64']:
            X[col] = X[col].fillna(X[col].median())
        else:
            X[col] = X[col].fillna('Unknown')
    
    # Obtener índices de features categóricas
    cat_features_indices = [i for i, col in enumerate(features_disponibles) if col in cat_features]
    
    return X, cat_features_indices


def validar_entrada_datos(data: Dict) -> Dict:
    """
    Valida y limpia los datos de entrada
    """
    # Campos requeridos
    required_fields = [
        'date', 'time', 'customer_id', 'vehicle_type', 
        'pickup_location', 'drop_location'
    ]
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    # Convertir a DataFrame para procesamiento
    df = pd.DataFrame([data])
    
    # Procesar datos
    df_procesado = procesar_datos_completo(df)
    
    return df_procesado.to_dict('records')[0]
