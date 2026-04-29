SELECT 'bronze_rows' AS check_name, count() AS value
FROM smart_dw.bronze_orders_raw

UNION ALL

SELECT 'silver_rows' AS check_name, count() AS value
FROM smart_dw.silver_orders_clean

UNION ALL

SELECT 'fact_sales_rows' AS check_name, count() AS value
FROM smart_dw.fact_sales

UNION ALL

SELECT 'null_order_id_in_silver' AS check_name, count() AS value
FROM smart_dw.silver_orders_clean
WHERE order_id IS NULL OR order_id = ''

UNION ALL

SELECT 'invalid_quantity_in_silver' AS check_name, count() AS value
FROM smart_dw.silver_orders_clean
WHERE quantity <= 0

UNION ALL

SELECT 'negative_revenue_in_silver' AS check_name, count() AS value
FROM smart_dw.silver_orders_clean
WHERE revenue < 0;

