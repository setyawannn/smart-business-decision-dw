CREATE TABLE IF NOT EXISTS smart_dw.dim_customer
ENGINE = MergeTree
ORDER BY customer_id
AS
SELECT DISTINCT
    customer_id,
    any(customer_name) AS customer_name,
    'Unknown' AS customer_segment,
    any(country) AS country,
    any(state) AS state,
    any(city) AS city
FROM smart_dw.silver_orders_clean
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

CREATE TABLE IF NOT EXISTS smart_dw.dim_product
ENGINE = MergeTree
ORDER BY product_id
AS
SELECT DISTINCT
    product_id,
    any(product_name) AS product_name,
    any(category) AS category,
    any(sub_category) AS sub_category,
    avgIf(revenue / quantity, quantity > 0) AS unit_price
FROM smart_dw.silver_orders_clean
WHERE product_id IS NOT NULL
GROUP BY product_id;

CREATE TABLE IF NOT EXISTS smart_dw.dim_channel
ENGINE = MergeTree
ORDER BY channel_id
AS
SELECT
    cityHash64(channel_name) AS channel_id,
    channel_name,
    'E-Commerce Channel' AS channel_type
FROM
(
    SELECT DISTINCT channel_name
    FROM smart_dw.silver_orders_clean
);

CREATE TABLE IF NOT EXISTS smart_dw.dim_time
ENGINE = MergeTree
ORDER BY date
AS
SELECT DISTINCT
    order_date AS date,
    toDayOfMonth(order_date) AS day,
    toMonth(order_date) AS month,
    formatDateTime(order_date, '%M') AS month_name,
    concat('Q', toString(toQuarter(order_date))) AS quarter,
    toYear(order_date) AS year
FROM smart_dw.silver_orders_clean;