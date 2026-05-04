CREATE TABLE IF NOT EXISTS smart_dw.customer_rfm
ENGINE = MergeTree
ORDER BY pseudo_customer_id
AS
WITH
    (SELECT max(order_date) FROM smart_dw.fact_sales) AS max_date
SELECT
    -- Create a pseudo customer id to simulate distribution for the showcase
    if(customer_id = 'Unknown', assumeNotNull(substring(order_id, length(order_id) - 3)), customer_id) AS pseudo_customer_id,
    dateDiff('day', max(order_date), max_date) AS recency,
    countDistinct(order_id) AS frequency,
    sum(revenue) AS monetary,
    multiIf(
        recency <= 30 AND frequency >= 3 AND monetary >= 500, 'Champions',
        recency <= 60 AND frequency >= 2, 'Loyal',
        recency > 90 AND monetary >= 200, 'At Risk',
        recency > 120, 'Hibernating',
        'Regular'
    ) AS segment_name
FROM smart_dw.fact_sales
GROUP BY pseudo_customer_id;

CREATE TABLE IF NOT EXISTS smart_dw.channel_performance_summary
ENGINE = MergeTree
ORDER BY channel_id
AS
SELECT
    channel_id,
    sum(revenue) AS total_revenue,
    sum(profit) AS total_profit,
    countDistinct(order_id) AS total_orders,
    if(sum(revenue) = 0, 0, sum(profit) / sum(revenue)) AS profit_margin
FROM smart_dw.fact_sales
GROUP BY channel_id;

CREATE TABLE IF NOT EXISTS smart_dw.product_profitability_summary
ENGINE = MergeTree
ORDER BY product_id
AS
SELECT
    product_id,
    sum(revenue) AS total_revenue,
    sum(profit) AS total_profit,
    sum(quantity) AS total_quantity,
    countDistinct(order_id) AS total_orders,
    if(sum(revenue) = 0, 0, sum(profit) / sum(revenue)) AS profit_margin
FROM smart_dw.fact_sales
GROUP BY product_id;

CREATE TABLE IF NOT EXISTS smart_dw.sales_forecast_ready
ENGINE = MergeTree
ORDER BY sales_date
AS
SELECT
    order_date AS sales_date,
    sum(revenue) AS total_revenue,
    sum(profit) AS total_profit,
    countDistinct(order_id) AS total_orders
FROM smart_dw.fact_sales
GROUP BY order_date;

CREATE TABLE IF NOT EXISTS smart_dw.geographic_performance_summary
ENGINE = MergeTree
ORDER BY state
AS
SELECT
    c.state AS state,
    c.city AS city,
    sum(f.revenue) AS total_revenue,
    sum(f.profit) AS total_profit,
    countDistinct(f.order_id) AS total_orders
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_customer AS c ON f.customer_id = c.customer_id
WHERE c.state != 'Unknown'
GROUP BY c.state, c.city;