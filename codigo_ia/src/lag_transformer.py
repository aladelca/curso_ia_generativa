from __future__ import annotations

from typing import List, Optional, Sequence

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


class LagByGroupDateTransformer(BaseEstimator, TransformerMixin):
    """
    Crea una columna de lag del agregado de `lag_column` por
    (nivel_agregacion, date_col), desplazando n días hacia atrás y uniendo
    al dataset original.

    - fit: calcula y guarda la tabla de lookup de lags (NO toca X).
    - transform: hace merge de X con la tabla de lags ya calculada
      (sin recomputar).
    """

    def __init__(
        self,
        nivel_agregacion: Sequence[str],
        n: int = 1,
        agg_func: str = "sum",
        date_col: str = "Date",
        lag_column: str = "Units Sold",
        ref_date: Optional[pd.Timestamp | str] = None,
        keep_original_date: bool = True,
    ) -> None:
        self.n = int(n)
        self.nivel_agregacion = list(nivel_agregacion)
        self.agg_func = agg_func
        self.date_col = date_col
        self.lag_column = lag_column
        self.ref_date = pd.to_datetime(ref_date).normalize()
        self.keep_original_date = keep_original_date

    def _validate_input(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        if self.date_col not in X.columns:
            raise ValueError(
                (f"'{self.date_col}' no está en columnas del " f"DataFrame.")
            )
        for col in self.nivel_agregacion + [self.lag_column]:
            if col not in X.columns:
                raise ValueError(f"'{col}' no está en columnas del DataFrame.")
        X[self.date_col] = pd.to_datetime(X[self.date_col])
        return X

    def _build_lookup(self, X: pd.DataFrame) -> pd.DataFrame:
        # Agrega por grupo + fecha
        # Preparamos el nombre de la columna agregada antes de agrupar
        # (evita problemas de tipo)
        label = "_".join(self.nivel_agregacion)
        lag_feat = f"lag_{self.lag_column}_{label}_{self.agg_func}_{self.n}"

        grp = (
            X.groupby(self.nivel_agregacion + [self.date_col], dropna=False)[
                self.lag_column
            ]
            .agg(self.agg_func)
            .reset_index(name=lag_feat)
        )

        # Desplaza la fecha hacia ATRÁS n días para construir la clave join
        grp["date_lag"] = grp[self.date_col] - pd.Timedelta(days=self.n)
        if self._effective_ref_date is not None:
            grp = grp.loc[grp[self.date_col] <= self._effective_ref_date]
        # Nos quedamos con las columnas necesarias para el merge en transform
        lookup_cols = self.nivel_agregacion + ["date_lag", lag_feat]
        return (
            grp[lookup_cols]
            .sort_values(self.nivel_agregacion + ["date_lag"])
            .reset_index(drop=True)
        )

    def fit(
        self, X: pd.DataFrame, y: Optional[pd.Series] = None
    ) -> "LagByGroupDateTransformer":
        X = self._validate_input(X)

        # ref_date efectiva: si no se pasó, tomamos hoy
        self._effective_ref_date = (
            self.ref_date
            if self.ref_date is not None
            else pd.Timestamp.today().normalize()
        )

        # Construye y guarda la tabla lookup
        self._lag_feature_name_ = (
            f"lag_{self.lag_column}_"
            f"{'_'.join(self.nivel_agregacion)}_{self.agg_func}_{self.n}"
        )
        self._lookup_df_ = self._build_lookup(X)

        # Guarda un set de columnas para chequeos
        self._input_columns_ = list(X.columns)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        check_is_fitted(self, attributes=["_lookup_df_", "_lag_feature_name_"])
        X = self._validate_input(X)

        # Clonamos para no tocar el original
        out = X.copy()

        # Si se quiere, recortamos los datos de entrada a fechas que no miren
        # al futuro respecto de la ref_date efectiva (evita fugas con fechas
        # futuras en X).

        # Preparamos claves de merge: izquierda usa
        # (nivel_agregacion + date_col), derecha usa
        # (nivel_agregacion + "date_lag") para traer el valor de hace n días.
        right_on = self.nivel_agregacion + ["date_lag"]
        left_on = self.nivel_agregacion + [self.date_col]

        out = out.merge(
            self._lookup_df_,
            how="left",
            left_on=left_on,
            right_on=right_on,
            sort=False,
        )

        # Limpieza de columnas auxiliares
        if not self.keep_original_date:
            out = out.drop(columns=[self.date_col], errors="ignore")
        out = out.drop(columns=["date_lag"], errors="ignore")

        return out

    def fit_transform(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        **fit_params: object,
    ) -> pd.DataFrame:
        return self.fit(X, y).transform(X)

    # Conveniencia
    def get_feature_names_out(
        self, input_features: Optional[List[str]] = None
    ) -> List[str]:
        check_is_fitted(self, attributes=["_lag_feature_name_"])
        return [self._lag_feature_name_]
