CREATE DATABASE IF NOT EXISTS smart_dw;

CREATE TABLE IF NOT EXISTS smart_dw.bronze_orders_raw
(
    order_id String,
    order_date String,
    customer_id String,
    customer_name String,
    product_id String,
    product_name String,
    category String,
    sub_category String,
    channel_name String,
    quantity String,
    revenue String,
    cost String,
    profit String,
    discount String,
    country String,
    state String,
    city String,
    ingestion_time DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (order_id);