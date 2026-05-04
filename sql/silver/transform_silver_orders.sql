DROP TABLE IF EXISTS smart_dw.silver_orders_clean;

CREATE TABLE smart_dw.silver_orders_clean
(
    order_id String,
    order_date Date,

    customer_id String,
    customer_name String,

    product_id String,
    product_name String,
    category String,
    sub_category String,

    channel_name String,

    quantity Int32,
    revenue Float64,
    cost Float64,
    profit Float64,
    discount Float64,

    country String,
    state String,
    city String,

    ingestion_time DateTime
)
ENGINE = MergeTree
ORDER BY (order_date, order_id);

INSERT INTO smart_dw.silver_orders_clean
SELECT
    raw_order_id AS order_id,

    toDate(
        concat('20', raw_yy, '-', raw_mm, '-', raw_dd)
    ) AS order_date,

    if(raw_customer_id = '', 'Unknown', raw_customer_id) AS customer_id,
    if(raw_customer_name = '', 'Unknown', raw_customer_name) AS customer_name,

    if(raw_product_id = '', 'Unknown', raw_product_id) AS product_id,
    if(raw_product_name = '', raw_product_id, raw_product_name) AS product_name,

    if(raw_category = '', 'Unknown', raw_category) AS category,
    if(raw_sub_category = '', 'Unknown', raw_sub_category) AS sub_category,

    if(raw_channel_name = '', 'Unknown', raw_channel_name) AS channel_name,

    toInt32OrZero(toString(raw_quantity)) AS quantity,
    toFloat64OrZero(toString(raw_revenue)) AS revenue,
    toFloat64OrZero(toString(raw_cost)) AS cost,
    toFloat64OrZero(toString(raw_profit)) AS profit,
    toFloat64OrZero(toString(raw_discount)) AS discount,

    if(raw_country = '', 'Unknown', raw_country) AS country,
    if(raw_state = '', 'Unknown', raw_state) AS state,
    if(raw_city = '', 'Unknown', raw_city) AS city,

    raw_ingestion_time AS ingestion_time
FROM
(
    SELECT
        toString(order_id) AS raw_order_id,
        toString(order_date) AS raw_order_date,

        substring(toString(order_date), 1, 2) AS raw_mm,
        substring(toString(order_date), 4, 2) AS raw_dd,
        substring(toString(order_date), 7, 2) AS raw_yy,

        toString(customer_id) AS raw_customer_id,
        toString(customer_name) AS raw_customer_name,

        toString(product_id) AS raw_product_id,
        toString(product_name) AS raw_product_name,
        toString(category) AS raw_category,
        toString(sub_category) AS raw_sub_category,

        toString(channel_name) AS raw_channel_name,

        toString(quantity) AS raw_quantity,
        toString(revenue) AS raw_revenue,
        toString(cost) AS raw_cost,
        toString(profit) AS raw_profit,
        toString(discount) AS raw_discount,

        toString(country) AS raw_country,
        toString(state) AS raw_state,
        toString(city) AS raw_city,

        ingestion_time AS raw_ingestion_time
    FROM smart_dw.bronze_orders_raw
) AS src
WHERE
    raw_order_id != ''
    AND raw_product_id != ''
    AND match(raw_order_date, '^[0-9]{2}-[0-9]{2}-[0-9]{2}$')
    AND toInt32OrZero(toString(raw_mm)) BETWEEN 1 AND 12
    AND toInt32OrZero(toString(raw_dd)) BETWEEN 1 AND 31
    AND toDateOrNull(concat('20', raw_yy, '-', raw_mm, '-', raw_dd)) IS NOT NULL
    AND toInt32OrZero(toString(raw_quantity)) > 0
    AND toFloat64OrZero(toString(raw_revenue)) >= 0;