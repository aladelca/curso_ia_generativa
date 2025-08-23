source("src/lag_transformer.R")


df <- tibble::tibble(
  Store = c("A", "A", "A", "A", "B", "B"),
  Date = as.Date(c(
    "2024-01-01", "2024-01-02", "2024-01-03",
    "2024-01-04", "2024-01-02", "2024-01-03"
  )),
  `Units Sold` = c(10, 12, 8, 15, 20, 18)
)

df

lag <- LagByGroupDateTransformerR$new(
  nivel_agregacion = c("Store"),
  n = -1,
  agg_func = "sum",
  date_col = "Date",
  lag_column = "Units Sold"
)

lag$fit(df)

output <- lag$transform(df)

output

lag$get_feature_names_out()
