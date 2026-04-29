CREATE TABLE IF NOT EXISTS smart_dw.fact_sales
ENGINE = MergeTree
PARTITION BY toYYYYMM(order_date)
ORDER BY (order_date, order_id, customer_id, product_id)
AS
SELECT
    order_id,
    order_date,
    customer_id,
    product_id,
    cityHash64(channel_name) AS channel_id,
    quantity,
    revenue,
    cost,
    profit,
    discount
FROM smart_dw.silver_orders_clean;