"""
Tests para el módulo de preprocessing
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, time
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from preprocessing import (
    limpiar_columnas, crear_variables_temporales, 
    crear_variables_comportamiento_simplificada,
    crear_variables_geograficas_simplificada,
    crear_variables_interaccion, procesar_datos_completo,
    preparar_features_para_modelo, validar_entrada_datos
)


class TestLimpiarColumnas:
    """Tests para limpieza de columnas"""
    
    def test_limpiar_columnas_espacios(self):
        """Test limpieza de espacios en nombres de columnas"""
        df = pd.DataFrame({
            'Pickup Location': [1, 2, 3],
            'Drop Location': [4, 5, 6],
            'Vehicle Type': ['A', 'B', 'C']
        })
        
        df_clean = limpiar_columnas(df)
        
        expected_columns = ['pickup_location', 'drop_location', 'vehicle_type']
        assert list(df_clean.columns) == expected_columns
    
    def test_limpiar_columnas_mayusculas(self):
        """Test conversión a minúsculas"""
        df = pd.DataFrame({
            'BOOKING_ID': [1, 2, 3],
            'Customer_ID': [4, 5, 6]
        })
        
        df_clean = limpiar_columnas(df)
        
        expected_columns = ['booking_id', 'customer_id']
        assert list(df_clean.columns) == expected_columns


class TestVariablesTemporales:
    """Tests para creación de variables temporales"""
    
    @pytest.fixture
    def sample_data(self):
        """Datos de prueba con fechas y horas"""
        return pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16', '2024-01-17'],  # Lun, Mar, Mier
            'time': ['08:30:00', '17:45:00', '22:15:00']
        })
    
    def test_crear_variables_temporales_basicas(self, sample_data):
        """Test creación de variables temporales básicas"""
        df_result = crear_variables_temporales(sample_data)
        
        # Verificar que se crearon las variables
        expected_vars = [
            'dia_semana', 'es_fin_semana', 'mes', 'dia_mes',
            'hora', 'minuto', 'periodo_dia', 'es_hora_pico'
        ]
        
        for var in expected_vars:
            assert var in df_result.columns
    
    def test_dia_semana_correcto(self, sample_data):
        """Test que el día de semana se calcula correctamente"""
        df_result = crear_variables_temporales(sample_data)
        
        # 2024-01-15 es lunes (día 0)
        assert df_result.iloc[0]['dia_semana'] == 0
        # 2024-01-16 es martes (día 1)
        assert df_result.iloc[1]['dia_semana'] == 1
    
    def test_es_fin_semana(self, sample_data):
        """Test identificación de fin de semana"""
        # Agregar un sábado
        sample_data_weekend = sample_data.copy()
        sample_data_weekend.loc[3] = ['2024-01-20', '10:00:00']  # Sábado
        
        df_result = crear_variables_temporales(sample_data_weekend)
        
        # Los primeros 3 días no son fin de semana
        assert df_result.iloc[0]['es_fin_semana'] == 0
        assert df_result.iloc[1]['es_fin_semana'] == 0
        assert df_result.iloc[2]['es_fin_semana'] == 0
        
        # El sábado sí es fin de semana
        assert df_result.iloc[3]['es_fin_semana'] == 1
    
    def test_periodo_dia(self, sample_data):
        """Test clasificación de períodos del día"""
        df_result = crear_variables_temporales(sample_data)
        
        assert df_result.iloc[0]['periodo_dia'] == 'Mañana'  # 08:30
        assert df_result.iloc[1]['periodo_dia'] == 'Tarde'   # 17:45
        assert df_result.iloc[2]['periodo_dia'] == 'Noche'   # 22:15
    
    def test_es_hora_pico(self, sample_data):
        """Test identificación de horas pico"""
        df_result = crear_variables_temporales(sample_data)
        
        assert df_result.iloc[0]['es_hora_pico'] == 1  # 08:30 - hora pico mañana
        assert df_result.iloc[1]['es_hora_pico'] == 1  # 17:45 - hora pico tarde
        assert df_result.iloc[2]['es_hora_pico'] == 0  # 22:15 - no es hora pico
    
    def test_variables_ciclicas(self, sample_data):
        """Test creación de variables cíclicas"""
        df_result = crear_variables_temporales(sample_data)
        
        ciclicas = ['hora_sin', 'hora_cos', 'dia_semana_sin', 'dia_semana_cos', 'mes_sin', 'mes_cos']
        
        for var in ciclicas:
            assert var in df_result.columns
            # Verificar que los valores están en el rango [-1, 1]
            assert df_result[var].min() >= -1
            assert df_result[var].max() <= 1


class TestVariablesComportamiento:
    """Tests para variables de comportamiento"""
    
    @pytest.fixture
    def sample_data_comportamiento(self):
        """Datos de prueba con ratings"""
        return pd.DataFrame({
            'customer_id': ['C1', 'C2', 'C3'],
            'driver_ratings': [4.8, 3.9, np.nan],
            'customer_rating': [4.5, 4.0, 4.9]
        })
    
    def test_rating_categorias(self, sample_data_comportamiento):
        """Test categorización de ratings"""
        df_result = crear_variables_comportamiento_simplificada(sample_data_comportamiento)
        
        assert df_result.iloc[0]['driver_rating_categoria'] == 'Excelente'  # 4.8
        assert df_result.iloc[1]['driver_rating_categoria'] == 'Bajo'       # 3.9
        assert df_result.iloc[2]['driver_rating_categoria'] == 'Sin_Rating' # NaN
        
        assert df_result.iloc[0]['customer_rating_categoria'] == 'Normal'    # 4.5
        assert df_result.iloc[1]['customer_rating_categoria'] == 'Normal'    # 4.0
        assert df_result.iloc[2]['customer_rating_categoria'] == 'Excelente' # 4.9


class TestVariablesGeograficas:
    """Tests para variables geográficas"""
    
    @pytest.fixture
    def sample_data_geograficas(self):
        """Datos de prueba con ubicaciones"""
        return pd.DataFrame({
            'pickup_location': ['Khan Market', 'Sector 50', 'CP'],
            'drop_location': ['Central Secretariat', 'Gurgaon', 'Cyber Hub']
        })
    
    def test_areas_centrales(self, sample_data_geograficas):
        """Test identificación de áreas centrales"""
        df_result = crear_variables_geograficas_simplificada(sample_data_geograficas)
        
        assert df_result.iloc[0]['pickup_central'] == 1  # Khan Market es central
        assert df_result.iloc[1]['pickup_central'] == 0  # Sector 50 no es central
        assert df_result.iloc[2]['pickup_central'] == 1  # CP es central
        
        assert df_result.iloc[0]['drop_central'] == 1    # Central Secretariat es central
        assert df_result.iloc[2]['drop_central'] == 1    # Cyber Hub es central
    
    def test_rutas_populares(self, sample_data_geograficas):
        """Test identificación de rutas populares"""
        df_result = crear_variables_geograficas_simplificada(sample_data_geograficas)
        
        # Una ruta es popular si pickup O drop es central
        assert df_result.iloc[0]['es_ruta_popular'] == 1  # Ambos centrales
        assert df_result.iloc[1]['es_ruta_popular'] == 0  # Ninguno central
        assert df_result.iloc[2]['es_ruta_popular'] == 1  # Ambos centrales


class TestVariablesInteraccion:
    """Tests para variables de interacción"""
    
    @pytest.fixture
    def sample_data_interaccion(self):
        """Datos de prueba para interacciones"""
        return pd.DataFrame({
            'pickup_central': [1, 0, 1],
            'es_hora_pico': [1, 1, 0],
            'cliente_problematico': [1, 0, 1],
            'es_fin_semana': [0, 1, 1]
        })
    
    def test_interacciones_basicas(self, sample_data_interaccion):
        """Test creación de variables de interacción"""
        df_result = crear_variables_interaccion(sample_data_interaccion)
        
        expected_vars = [
            'centro_en_hora_pico', 'problematico_fin_semana', 
            'problema_en_hora_pico', 'desbalance_demanda_oferta'
        ]
        
        for var in expected_vars:
            assert var in df_result.columns
    
    def test_centro_en_hora_pico(self, sample_data_interaccion):
        """Test interacción centro en hora pico"""
        df_result = crear_variables_interaccion(sample_data_interaccion)
        
        assert df_result.iloc[0]['centro_en_hora_pico'] == 1  # pickup_central=1 Y es_hora_pico=1
        assert df_result.iloc[1]['centro_en_hora_pico'] == 0  # pickup_central=0
        assert df_result.iloc[2]['centro_en_hora_pico'] == 0  # es_hora_pico=0


class TestProcesarDatosCompleto:
    """Tests para el pipeline completo"""
    
    @pytest.fixture
    def sample_data_completo(self):
        """Datos de prueba completos"""
        return pd.DataFrame({
            'Date': ['2024-01-15'],
            'Time': ['08:30:00'],
            'Customer ID': ['C123'],
            'Vehicle Type': ['Auto'],
            'Pickup Location': ['Khan Market'],
            'Drop Location': ['CP'],
            'Booking Status': ['No Driver Found'],
            'Driver Ratings': [4.5],
            'Customer Rating': [4.2]
        })
    
    def test_pipeline_completo(self, sample_data_completo):
        """Test que el pipeline completo funciona"""
        df_result = procesar_datos_completo(sample_data_completo)
        
        # Verificar que se limpiaron las columnas
        assert 'pickup_location' in df_result.columns
        assert 'vehicle_type' in df_result.columns
        
        # Verificar que se creó el target
        assert 'target' in df_result.columns
        assert df_result.iloc[0]['target'] == 1  # "No Driver Found" = 1
        
        # Verificar que se crearon variables temporales
        assert 'es_hora_pico' in df_result.columns
        assert 'periodo_dia' in df_result.columns
        
        # Verificar que se crearon variables geográficas
        assert 'pickup_central' in df_result.columns


class TestValidarEntradaDatos:
    """Tests para validación de datos de entrada"""
    
    def test_validar_entrada_completa(self):
        """Test validación con datos completos"""
        data = {
            'date': '2024-01-15',
            'time': '08:30:00',
            'customer_id': 'C123',
            'vehicle_type': 'Auto',
            'pickup_location': 'Khan Market',
            'drop_location': 'CP'
        }
        
        result = validar_entrada_datos(data)
        
        # Debe retornar un dict procesado
        assert isinstance(result, dict)
        assert 'pickup_location' in result
    
    def test_validar_entrada_campos_faltantes(self):
        """Test validación con campos faltantes"""
        data = {
            'date': '2024-01-15',
            'time': '08:30:00'
            # Faltan campos requeridos
        }
        
        with pytest.raises(ValueError, match="Campo requerido faltante"):
            validar_entrada_datos(data)


class TestPrepararFeaturesParaModelo:
    """Tests para preparación de features para el modelo"""
    
    @pytest.fixture
    def sample_data_features(self):
        """Datos procesados para testing"""
        return pd.DataFrame({
            'vehicle_type': ['Auto', 'Bike'],
            'periodo_dia': ['Mañana', 'Tarde'],
            'hora': [8, 17],
            'es_hora_pico': [1, 1],
            'pickup_central': [1, 0],
            'avg_vtat': [5.0, np.nan],
            'target': [0, 1]
        })
    
    def test_preparar_features(self, sample_data_features):
        """Test preparación de features"""
        X, cat_features_indices = preparar_features_para_modelo(sample_data_features)
        
        # Verificar que se retorna DataFrame
        assert isinstance(X, pd.DataFrame)
        assert isinstance(cat_features_indices, list)
        
        # Verificar que se rellenaron los NaN
        assert not X.isnull().any().any()
        
        # Verificar que se identificaron features categóricas
        assert len(cat_features_indices) > 0


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
