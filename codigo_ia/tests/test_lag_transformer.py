import numpy as np
import pandas as pd
from lag_transformer import LagByGroupDateTransformer  # type: ignore


def _make_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(
                [
                    "2025-08-01",
                    "2025-08-02",
                    "2025-08-03",
                ]
            ),
            "Store ID": ["A", "A", "A"],
            "Product ID": ["X", "X", "X"],
            "Units Sold": [10, 5, 2],
        }
    )


def test_lag_values_forward_behavior() -> None:
    """Verifica que el lag calculado por la clase aparece con los valores esperados.

    Nota: la implementación actual calcula una tabla agregada por fecha y crea
    una columna `date_lag = Date - n` en la tabla de lookup; al hacer merge de
    (nivel_agregacion + Date) con (nivel_agregacion + date_lag) el valor
    asociado para una fila con fecha D corresponde al agregado en la fecha
    D + n (comportamiento 'forward' según la implementación actual).
    """
    df = _make_df()

    tr = LagByGroupDateTransformer(nivel_agregacion=["Store ID", "Product ID"], n=1)
    out = tr.fit_transform(df.copy())

    lag_name = tr._lag_feature_name_
    assert lag_name in out.columns

    # Esperado según la lógica explicada arriba: row 0 -> value at 2025-08-02 (5),
    # row 1 -> value at 2025-08-03 (2), row 2 -> no dato (NaN)
    expected = [5.0, 2.0, np.nan]

    actual = out[lag_name].astype(float).tolist()

    # Comparación element-wise para manejar NaNs
    for a, e in zip(actual, expected, strict=False):
        if pd.isna(e):
            assert pd.isna(a)
        else:
            assert a == e


def test_keep_original_date_flag() -> None:
    df = _make_df()
    tr = LagByGroupDateTransformer(
        nivel_agregacion=["Store ID", "Product ID"], n=1, keep_original_date=False
    )
    out = tr.fit_transform(df.copy())

    # El transform con keep_original_date=False debe eliminar la columna Date
    assert "Date" not in out.columns
    # Y debe contener la columna lag
    assert tr._lag_feature_name_ in out.columns
