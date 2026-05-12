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
    countDistinct(order_id) AS total_orders,
    sum(quantity) AS total_quantity
FROM smart_dw.fact_sales
GROUP BY order_date;

CREATE TABLE IF NOT EXISTS smart_dw.kpi_daily_snapshot
ENGINE = MergeTree
ORDER BY snapshot_date
AS
SELECT
    snapshot_date,
    revenue,
    orders,
    quantity,
    if(orders = 0, 0, revenue / orders) AS aov
FROM
(
    SELECT
        order_date AS snapshot_date,
        sum(revenue) AS revenue,
        countDistinct(order_id) AS orders,
        sum(quantity) AS quantity
    FROM smart_dw.fact_sales
    GROUP BY order_date
);

CREATE TABLE IF NOT EXISTS smart_dw.geographic_daily_summary
ENGINE = MergeTree
ORDER BY (order_date, state)
AS
SELECT
    order_date,
    CASE
        WHEN upper(state) IN ('MAHARASHTRA') THEN 'IN-MH'
        WHEN upper(state) IN ('KARNATAKA') THEN 'IN-KA'
        WHEN upper(state) IN ('TAMIL NADU') THEN 'IN-TN'
        WHEN upper(state) IN ('TELANGANA') THEN 'IN-TG'
        WHEN upper(state) IN ('UTTAR PRADESH') THEN 'IN-UP'
        WHEN upper(state) IN ('DELHI', 'NEW DELHI') THEN 'IN-DL'
        WHEN upper(state) IN ('KERALA') THEN 'IN-KL'
        WHEN upper(state) IN ('WEST BENGAL') THEN 'IN-WB'
        WHEN upper(state) IN ('ANDHRA PRADESH') THEN 'IN-AP'
        WHEN upper(state) IN ('GUJARAT') THEN 'IN-GJ'
        WHEN upper(state) IN ('HARYANA') THEN 'IN-HR'
        WHEN upper(state) IN ('RAJASTHAN', 'RJ', 'RAJSHTHAN', 'RAJSTHAN') THEN 'IN-RJ'
        WHEN upper(state) IN ('MADHYA PRADESH') THEN 'IN-MP'
        WHEN upper(state) IN ('ODISHA', 'ORISSA') THEN 'IN-OR'
        WHEN upper(state) IN ('BIHAR') THEN 'IN-BR'
        WHEN upper(state) IN ('PUNJAB', 'PB', 'PUNJAB/MOHALI/ZIRAKPUR') THEN 'IN-PB'
        WHEN upper(state) IN ('ASSAM') THEN 'IN-AS'
        WHEN upper(state) IN ('UTTARAKHAND') THEN 'IN-UT'
        WHEN upper(state) IN ('JHARKHAND') THEN 'IN-JH'
        WHEN upper(state) IN ('GOA') THEN 'IN-GA'
        WHEN upper(state) IN ('CHHATTISGARH') THEN 'IN-CT'
        WHEN upper(state) IN ('HIMACHAL PRADESH') THEN 'IN-HP'
        WHEN upper(state) IN ('JAMMU & KASHMIR') THEN 'IN-JK'
        WHEN upper(state) IN ('PUDUCHERRY', 'PONDICHERRY') THEN 'IN-PY'
        WHEN upper(state) IN ('CHANDIGARH') THEN 'IN-CH'
        WHEN upper(state) IN ('MANIPUR') THEN 'IN-MN'
        WHEN upper(state) IN ('ANDAMAN & NICOBAR') THEN 'IN-AN'
        WHEN upper(state) IN ('MEGHALAYA') THEN 'IN-ML'
        WHEN upper(state) IN ('SIKKIM') THEN 'IN-SK'
        WHEN upper(state) IN ('NAGALAND', 'NL') THEN 'IN-NL'
        WHEN upper(state) IN ('TRIPURA') THEN 'IN-TR'
        WHEN upper(state) IN ('ARUNACHAL PRADESH', 'AR') THEN 'IN-AR'
        WHEN upper(state) IN ('MIZORAM') THEN 'IN-MZ'
        WHEN upper(state) IN ('DADRA AND NAGAR') THEN 'IN-DN'
        WHEN upper(state) IN ('LADAKH') THEN 'IN-LA'
        WHEN upper(state) IN ('LAKSHADWEEP') THEN 'IN-LD'
        ELSE 'UNKNOWN'
    END AS iso_code,
    state,
    sum(revenue) AS total_revenue,
    countDistinct(order_id) AS total_orders
FROM smart_dw.silver_orders_clean
WHERE state != 'Unknown' AND state != ''
GROUP BY order_date, state;

CREATE TABLE IF NOT EXISTS smart_dw.channel_monthly_summary
ENGINE = MergeTree
ORDER BY (snapshot_month, channel_name)
AS
SELECT
    toStartOfMonth(f.order_date) AS snapshot_month,
    ifNull(c.channel_name, 'Unknown') AS channel_name,
    sum(f.revenue) AS total_revenue,
    countDistinct(f.order_id) AS total_orders
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_channel AS c ON f.channel_id = c.channel_id
GROUP BY snapshot_month, channel_name;

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
