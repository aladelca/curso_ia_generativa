#' LagByGroupDateTransformerR: transformador de lags por grupo y fecha
#'
#' Crea una característica lag agregada (sum/mean/...) por (`nivel_agregacion`, `date_col`),
#' desplazada `n` días hacia atrás, y la une al dataset original.
#'
#' - fit(): calcula y guarda la tabla de lookup (no modifica X)
#' - transform(): hace join de X con la tabla de lags
#'
suppressPackageStartupMessages({
  requireNamespace("R6", quietly = TRUE)
  requireNamespace("dplyr", quietly = TRUE)
  requireNamespace("lubridate", quietly = TRUE)
})

LagByGroupDateTransformerR <- R6::R6Class( # nolint: object_name_linter
  classname = "LagByGroupDateTransformerR",
  public = list(
    nivel_agregacion = NULL,
    n = NULL,
    agg_func = NULL,
    date_col = NULL,
    lag_column = NULL,
    ref_date = NULL,
    keep_original_date = NULL,
    initialize = function(nivel_agregacion,
                          n = 1,
                          agg_func = "sum",
                          date_col = "Date",
                          lag_column = "Units Sold",
                          ref_date = NULL,
                          keep_original_date = TRUE) {
      stopifnot(is.character(nivel_agregacion), length(nivel_agregacion) >= 1)
      self$nivel_agregacion <- nivel_agregacion
      self$n <- as.integer(n)
      self$agg_func <- match.arg(agg_func, c("sum", "mean", "median", "max", "min"))
      self$date_col <- as.character(date_col)
      self$lag_column <- as.character(lag_column)
      self$ref_date <- if (!is.null(ref_date)) as.Date(ref_date) else NULL
      self$keep_original_date <- isTRUE(keep_original_date)
    },
    fit = function(x) {
      x <- private$validate_input(x)
      private$effective_ref_date <- if (!is.null(self$ref_date)) self$ref_date else Sys.Date()

      label <- paste(self$nivel_agregacion, collapse = "_")
      private$lag_feature_name <- sprintf(
        "lag_%s_%s_%s_%d",
        self$lag_column, label, self$agg_func, self$n
      )

      private$lookup_df <- private$build_lookup(x)
      private$input_columns <- colnames(x)
      invisible(self)
    },
    transform = function(x) {
      if (is.null(private$lookup_df) || is.null(private$lag_feature_name)) {
        stop("El transformador no está ajustado. Llama a fit() primero.")
      }
      x <- private$validate_input(x)

      # Join: izquierda (X) con derecha (lookup) mapeando date_col <- date_lag
      by_cols <- c(self$nivel_agregacion, self$date_col)
      right <- private$lookup_df
      # renombrar date_lag a date_col para que el join sea directo
      right2 <- dplyr::rename(right, !!self$date_col := .data$date_lag)

      out <- dplyr::left_join(x, right2, by = by_cols)

      if (!self$keep_original_date) {
        out <- dplyr::select(out, -dplyr::all_of(self$date_col))
      }
      out
    },
    fit_transform = function(x) {
      self$fit(x)
      self$transform(x)
    },
    get_feature_names_out = function() {
      if (is.null(private$lag_feature_name)) {
        stop("El transformador no está ajustado. Llama a fit() primero.")
      }
      private$lag_feature_name
    }
  ),
  private = list(
    input_columns = NULL,
    lookup_df = NULL,
    lag_feature_name = NULL,
    effective_ref_date = NULL,
    validate_input = function(x) {
      stopifnot(is.data.frame(x))
      cols_needed <- c(self$nivel_agregacion, self$date_col, self$lag_column)
      falta <- setdiff(cols_needed, colnames(x))
      if (length(falta) > 0) {
        stop(sprintf("Faltan columnas en X: %s", paste(falta, collapse = ", ")))
      }
      x[[self$date_col]] <- as.Date(x[[self$date_col]])
      x
    },
    build_lookup = function(x) {
      label <- paste(self$nivel_agregacion, collapse = "_")
      lag_feat <- private$lag_feature_name

      agg_fun <- switch(self$agg_func,
        sum = sum,
        mean = mean,
        median = median,
        max = max,
        min = min
      )

      grp <- x |>
        dplyr::group_by(dplyr::across(dplyr::all_of(c(self$nivel_agregacion, self$date_col)))) |>
        dplyr::summarise(
          .agg = agg_fun(.data[[self$lag_column]], na.rm = TRUE),
          .groups = "drop"
        ) |>
        dplyr::rename(!!lag_feat := .data$.agg)

      grp <- grp |>
        dplyr::mutate(date_lag = .data[[self$date_col]] - lubridate::days(self$n))

      if (!is.null(private$effective_ref_date)) {
        grp <- dplyr::filter(grp, .data[[self$date_col]] <= private$effective_ref_date)
      }

      lookup_cols <- c(self$nivel_agregacion, "date_lag", lag_feat)
      grp |>
        dplyr::select(dplyr::all_of(lookup_cols)) |>
        dplyr::arrange(dplyr::across(dplyr::all_of(c(self$nivel_agregacion, "date_lag")))) |>
        as.data.frame()
    }
  )
)
