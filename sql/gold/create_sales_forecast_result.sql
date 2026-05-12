CREATE TABLE IF NOT EXISTS smart_dw.sales_forecast_result
(
    sales_date Date,
    metric_name String,
    actual_value Nullable(Float64),
    forecast_value Nullable(Float64),
    lower_bound Nullable(Float64),
    upper_bound Nullable(Float64),
    model_name String,
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (metric_name, sales_date);