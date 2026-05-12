import json
import os
from calendar import monthrange
from datetime import date
from urllib.parse import quote_plus

import clickhouse_connect
from superset.app import create_app
from superset.extensions import db


DATABASE_NAME = "Smart DW ClickHouse"
CLICKHOUSE_USER = quote_plus(os.getenv("CLICKHOUSE_USER", "superset"))
CLICKHOUSE_PASSWORD = quote_plus(os.getenv("CLICKHOUSE_PASSWORD", "superset_lokal_kamu"))

DATABASE_URI = (
    f"clickhousedb+connect://{CLICKHOUSE_USER}:"
    f"{CLICKHOUSE_PASSWORD}@"
    f"{os.getenv('CLICKHOUSE_HOST', 'clickhouse')}:"
    f"{os.getenv('CLICKHOUSE_HTTP_PORT', '8123')}/"
    f"{os.getenv('CLICKHOUSE_DATABASE', 'smart_dw')}"
)
SCHEMA = os.getenv("CLICKHOUSE_DATABASE", "smart_dw")
DASHBOARD_TITLE = "Smart Business Decision Dashboard"
CHART_PREFIX = "SBD - "


DATASETS = {
    "fact_sales": {
        "order_id": "String",
        "order_date": "Date",
        "customer_id": "String",
        "product_id": "String",
        "channel_id": "UInt64",
        "quantity": "Int32",
        "revenue": "Float64",
        "cost": "Float64",
        "profit": "Float64",
        "discount": "Float64",
    },
    "silver_orders_clean": {
        "order_id": "String",
        "order_date": "Date",
        "customer_id": "String",
        "customer_name": "String",
        "product_id": "String",
        "product_name": "String",
        "category": "String",
        "sub_category": "String",
        "channel_name": "String",
        "quantity": "Int32",
        "revenue": "Float64",
        "cost": "Float64",
        "profit": "Float64",
        "discount": "Float64",
        "country": "String",
        "state": "String",
        "city": "String",
    },
    "dim_product": {
        "product_id": "String",
        "product_name": "String",
        "category": "String",
        "sub_category": "String",
        "unit_price": "Float64",
    },
    "dim_channel": {
        "channel_id": "UInt64",
        "channel_name": "String",
        "channel_type": "String",
    },
    "dim_time": {
        "date": "Date",
        "day": "UInt8",
        "month": "UInt8",
        "month_name": "String",
        "quarter": "String",
        "year": "UInt16",
    },
    "customer_rfm": {
        "customer_id": "String",
        "recency": "Int64",
        "frequency": "UInt64",
        "monetary": "Float64",
        "segment_name": "String",
    },
    "channel_performance_summary": {
        "channel_id": "UInt64",
        "total_revenue": "Float64",
        "total_profit": "Float64",
        "total_orders": "UInt64",
        "profit_margin": "Float64",
    },
    "product_profitability_summary": {
        "product_id": "String",
        "total_revenue": "Float64",
        "total_profit": "Float64",
        "total_quantity": "Int64",
        "total_orders": "UInt64",
        "profit_margin": "Float64",
    },
    "sales_forecast_ready": {
        "sales_date": "Date",
        "total_revenue": "Float64",
        "total_profit": "Float64",
        "total_orders": "UInt64",
        "total_quantity": "Int64",
    },
    "sales_forecast_result": {
        "sales_date": "Date",
        "metric_name": "String",
        "actual_value": "Nullable(Float64)",
        "forecast_value": "Nullable(Float64)",
        "lower_bound": "Nullable(Float64)",
        "upper_bound": "Nullable(Float64)",
        "model_name": "String",
        "created_at": "DateTime",
    },
    "kpi_daily_snapshot": {
        "snapshot_date": "Date",
        "revenue": "Float64",
        "orders": "UInt64",
        "quantity": "Int64",
        "aov": "Float64",
    },
    "geographic_daily_summary": {
        "order_date": "Date",
        "iso_code": "String",
        "state": "String",
        "total_revenue": "Float64",
        "total_orders": "UInt64",
    },
    "channel_monthly_summary": {
        "snapshot_month": "Date",
        "channel_name": "String",
        "total_revenue": "Float64",
        "total_orders": "UInt64",
    },
}

DATASET_MAIN_DTTS = {
    "fact_sales": "order_date",
    "silver_orders_clean": "order_date",
    "sales_forecast_ready": "sales_date",
    "sales_forecast_result": "sales_date",
    "kpi_daily_snapshot": "snapshot_date",
    "geographic_daily_summary": "order_date",
    "channel_monthly_summary": "snapshot_month",
    "vw_revenue_by_category": "order_date",
    "vw_revenue_by_sub_category": "order_date",
    "vw_top_products_by_revenue": "order_date",
    "vw_channel_performance": "order_date",
    "vw_geographic_performance": "order_date",
    "vw_kpi_monthly_status": "snapshot_month",
    "vw_kpi_daily_comparison": "snapshot_date",
    "vw_monthly_channel_revenue": "snapshot_month",
    "vw_top_states_revenue": "order_date",
}

DATASET_CUSTOM_METRICS = {
    "fact_sales": {
        "total_revenue": "SUM(revenue)",
        "total_profit": "SUM(profit)",
        "total_quantity_sold": "SUM(quantity)",
        "total_orders": "COUNT(DISTINCT order_id)",
        "average_order_value": (
            "CASE WHEN COUNT(DISTINCT order_id) = 0 THEN 0 "
            "ELSE SUM(revenue) / COUNT(DISTINCT order_id) END"
        ),
    },
    "kpi_daily_snapshot": {
        "total_revenue": "SUM(revenue)",
        "total_orders": "SUM(orders)",
        "total_quantity_sold": "SUM(quantity)",
        "average_order_value": "AVG(aov)",
    },
    "sales_forecast_result": {
        "actual_value": "SUM(actual_value)",
        "forecast_value": "SUM(forecast_value)",
        "lower_bound": "SUM(lower_bound)",
        "upper_bound": "SUM(upper_bound)",
    },
}

VIRTUAL_DATASETS = {
    "vw_revenue_by_category": {
        "sql": """
SELECT
    f.order_date AS order_date,
    ifNull(p.category, 'Unknown') AS category,
    sum(f.revenue) AS total_revenue,
    sum(f.quantity) AS total_quantity
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_product AS p ON f.product_id = p.product_id
GROUP BY f.order_date, category
ORDER BY total_revenue DESC
""",
        "columns": {
            "order_date": "Date",
            "category": "String",
            "total_revenue": "Float64",
            "total_quantity": "Int64",
        },
    },
    "vw_revenue_by_sub_category": {
        "sql": """
SELECT
    f.order_date AS order_date,
    ifNull(p.sub_category, 'Unknown') AS sub_category,
    sum(f.revenue) AS total_revenue,
    sum(f.quantity) AS total_quantity
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_product AS p ON f.product_id = p.product_id
GROUP BY f.order_date, sub_category
ORDER BY total_revenue DESC
""",
        "columns": {
            "order_date": "Date",
            "sub_category": "String",
            "total_revenue": "Float64",
            "total_quantity": "Int64",
        },
    },
    "vw_top_products_by_revenue": {
        "sql": """
SELECT
    f.order_date AS order_date,
    ifNull(p.product_name, 'Unknown') AS product_name,
    ifNull(p.category, 'Unknown') AS category,
    sum(f.revenue) AS total_revenue,
    sum(f.quantity) AS total_quantity,
    countDistinct(f.order_id) AS total_orders
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_product AS p ON f.product_id = p.product_id
GROUP BY f.order_date, product_name, category
ORDER BY total_revenue DESC
""",
        "columns": {
            "order_date": "Date",
            "product_name": "String",
            "category": "String",
            "total_revenue": "Float64",
            "total_quantity": "Int64",
            "total_orders": "UInt64",
        },
    },
    "vw_channel_performance": {
        "sql": """
SELECT
    f.order_date AS order_date,
    ifNull(c.channel_name, 'Unknown') AS channel_name,
    ifNull(c.channel_type, 'Unknown') AS channel_type,
    sum(f.revenue) AS total_revenue,
    countDistinct(f.order_id) AS total_orders
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_channel AS c ON f.channel_id = c.channel_id
GROUP BY f.order_date, channel_name, channel_type
ORDER BY total_revenue DESC
""",
        "columns": {
            "order_date": "Date",
            "channel_name": "String",
            "channel_type": "String",
            "total_revenue": "Float64",
            "total_orders": "UInt64",
        },
    },
    "vw_customer_segment_distribution": {
        "sql": """
SELECT
    segment_name,
    count() AS customers,
    sum(monetary) AS total_monetary
FROM smart_dw.customer_rfm
GROUP BY segment_name
ORDER BY customers DESC
""",
        "columns": {
            "segment_name": "String",
            "customers": "UInt64",
            "total_monetary": "Float64",
        },
    },
    "vw_geographic_performance": {
        "sql": """
SELECT
    order_date AS order_date,
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
GROUP BY order_date, state
ORDER BY total_revenue DESC
""",
        "columns": {
            "order_date": "Date",
            "iso_code": "String",
            "state": "String",
            "total_revenue": "Float64",
            "total_orders": "UInt64",
        },
    },
    "vw_kpi_monthly_status": {
        "sql": """
WITH monthly AS (
    SELECT
        toStartOfMonth(order_date) AS snapshot_month,
        sum(revenue) AS total_revenue,
        countDistinct(order_id) AS total_orders,
        sum(quantity) AS total_quantity_sold,
        if(countDistinct(order_id) = 0, 0, sum(revenue) / countDistinct(order_id)) AS average_order_value
    FROM smart_dw.fact_sales
    GROUP BY snapshot_month
),
monthly_with_previous AS (
    SELECT
        current.snapshot_month AS snapshot_month,
        current.total_revenue AS total_revenue,
        current.total_orders AS total_orders,
        current.total_quantity_sold AS total_quantity_sold,
        current.average_order_value AS average_order_value,
        previous.total_revenue AS previous_total_revenue,
        previous.total_orders AS previous_total_orders,
        previous.total_quantity_sold AS previous_total_quantity_sold,
        previous.average_order_value AS previous_average_order_value
    FROM monthly AS current
    LEFT JOIN monthly AS previous
        ON previous.snapshot_month = addMonths(current.snapshot_month, -1)
)
SELECT
    snapshot_month,
    'Revenue' AS kpi_name,
    total_revenue AS current_value,
    previous_total_revenue AS previous_value,
    total_revenue - ifNull(previous_total_revenue, 0) AS delta_value,
    if(previous_total_revenue IS NULL OR previous_total_revenue = 0, NULL, (total_revenue - previous_total_revenue) / previous_total_revenue) AS delta_pct,
    if(previous_total_revenue IS NULL, 'No Baseline', if(total_revenue >= previous_total_revenue, 'Up', 'Down')) AS trend_direction,
    if(previous_total_revenue IS NULL, 'No Baseline', if(total_revenue >= previous_total_revenue, 'Meets Minimum', 'Below Minimum')) AS minimum_status
FROM monthly_with_previous
UNION ALL
SELECT
    snapshot_month,
    'Orders' AS kpi_name,
    toFloat64(total_orders) AS current_value,
    toFloat64(previous_total_orders) AS previous_value,
    toFloat64(total_orders - ifNull(previous_total_orders, 0)) AS delta_value,
    if(previous_total_orders IS NULL OR previous_total_orders = 0, NULL, toFloat64(total_orders - previous_total_orders) / previous_total_orders) AS delta_pct,
    if(previous_total_orders IS NULL, 'No Baseline', if(total_orders >= previous_total_orders, 'Up', 'Down')) AS trend_direction,
    if(previous_total_orders IS NULL, 'No Baseline', if(total_orders >= previous_total_orders, 'Meets Minimum', 'Below Minimum')) AS minimum_status
FROM monthly_with_previous
UNION ALL
SELECT
    snapshot_month,
    'Quantity' AS kpi_name,
    toFloat64(total_quantity_sold) AS current_value,
    toFloat64(previous_total_quantity_sold) AS previous_value,
    toFloat64(total_quantity_sold - ifNull(previous_total_quantity_sold, 0)) AS delta_value,
    if(previous_total_quantity_sold IS NULL OR previous_total_quantity_sold = 0, NULL, toFloat64(total_quantity_sold - previous_total_quantity_sold) / previous_total_quantity_sold) AS delta_pct,
    if(previous_total_quantity_sold IS NULL, 'No Baseline', if(total_quantity_sold >= previous_total_quantity_sold, 'Up', 'Down')) AS trend_direction,
    if(previous_total_quantity_sold IS NULL, 'No Baseline', if(total_quantity_sold >= previous_total_quantity_sold, 'Meets Minimum', 'Below Minimum')) AS minimum_status
FROM monthly_with_previous
UNION ALL
SELECT
    snapshot_month,
    'AOV' AS kpi_name,
    average_order_value AS current_value,
    previous_average_order_value AS previous_value,
    average_order_value - ifNull(previous_average_order_value, 0) AS delta_value,
    if(previous_average_order_value IS NULL OR previous_average_order_value = 0, NULL, (average_order_value - previous_average_order_value) / previous_average_order_value) AS delta_pct,
    if(previous_average_order_value IS NULL, 'No Baseline', if(average_order_value >= previous_average_order_value, 'Up', 'Down')) AS trend_direction,
    if(previous_average_order_value IS NULL, 'No Baseline', if(average_order_value >= previous_average_order_value, 'Meets Minimum', 'Below Minimum')) AS minimum_status
FROM monthly_with_previous
""",
        "columns": {
            "snapshot_month": "Date",
            "kpi_name": "String",
            "current_value": "Float64",
            "previous_value": "Nullable(Float64)",
            "delta_value": "Float64",
            "delta_pct": "Nullable(Float64)",
            "trend_direction": "String",
            "minimum_status": "String",
        },
    },
    "vw_kpi_daily_comparison": {
        "sql": """
WITH daily AS (
    SELECT
        order_date AS snapshot_date,
        sum(revenue) AS total_revenue,
        countDistinct(order_id) AS total_orders,
        sum(quantity) AS total_quantity_sold,
        if(countDistinct(order_id) = 0, 0, sum(revenue) / countDistinct(order_id)) AS average_order_value
    FROM smart_dw.fact_sales
    GROUP BY snapshot_date
),
daily_with_previous AS (
    SELECT
        current.snapshot_date AS snapshot_date,
        current.total_revenue AS total_revenue,
        current.total_orders AS total_orders,
        current.total_quantity_sold AS total_quantity_sold,
        current.average_order_value AS average_order_value,
        previous.total_revenue AS previous_total_revenue,
        previous.total_orders AS previous_total_orders,
        previous.total_quantity_sold AS previous_total_quantity_sold,
        previous.average_order_value AS previous_average_order_value
    FROM daily AS current
    LEFT JOIN daily AS previous
        ON previous.snapshot_date = addDays(current.snapshot_date, -1)
)
SELECT
    snapshot_date,
    'Revenue' AS kpi_name,
    total_revenue AS current_value,
    previous_total_revenue AS previous_value,
    total_revenue - ifNull(previous_total_revenue, 0) AS delta_value,
    if(previous_total_revenue IS NULL OR previous_total_revenue = 0, NULL, (total_revenue - previous_total_revenue) / previous_total_revenue) AS delta_pct
FROM daily_with_previous
UNION ALL
SELECT
    snapshot_date,
    'Orders' AS kpi_name,
    toFloat64(total_orders) AS current_value,
    toFloat64(previous_total_orders) AS previous_value,
    toFloat64(total_orders - ifNull(previous_total_orders, 0)) AS delta_value,
    if(previous_total_orders IS NULL OR previous_total_orders = 0, NULL, toFloat64(total_orders - previous_total_orders) / previous_total_orders) AS delta_pct
FROM daily_with_previous
UNION ALL
SELECT
    snapshot_date,
    'Quantity' AS kpi_name,
    toFloat64(total_quantity_sold) AS current_value,
    toFloat64(previous_total_quantity_sold) AS previous_value,
    toFloat64(total_quantity_sold - ifNull(previous_total_quantity_sold, 0)) AS delta_value,
    if(previous_total_quantity_sold IS NULL OR previous_total_quantity_sold = 0, NULL, toFloat64(total_quantity_sold - previous_total_quantity_sold) / previous_total_quantity_sold) AS delta_pct
FROM daily_with_previous
UNION ALL
SELECT
    snapshot_date,
    'AOV' AS kpi_name,
    average_order_value AS current_value,
    previous_average_order_value AS previous_value,
    average_order_value - ifNull(previous_average_order_value, 0) AS delta_value,
    if(previous_average_order_value IS NULL OR previous_average_order_value = 0, NULL, (average_order_value - previous_average_order_value) / previous_average_order_value) AS delta_pct
FROM daily_with_previous
""",
        "columns": {
            "snapshot_date": "Date",
            "kpi_name": "String",
            "current_value": "Float64",
            "previous_value": "Nullable(Float64)",
            "delta_value": "Float64",
            "delta_pct": "Nullable(Float64)",
        },
    },
    "vw_monthly_channel_revenue": {
        "sql": """
SELECT
    toStartOfMonth(f.order_date) AS snapshot_month,
    ifNull(c.channel_name, 'Unknown') AS channel_name,
    sum(f.revenue) AS total_revenue,
    countDistinct(f.order_id) AS total_orders
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_channel AS c ON f.channel_id = c.channel_id
GROUP BY snapshot_month, channel_name
ORDER BY snapshot_month, total_revenue DESC
""",
        "columns": {
            "snapshot_month": "Date",
            "channel_name": "String",
            "total_revenue": "Float64",
            "total_orders": "UInt64",
        },
    },
    "vw_top_states_revenue": {
        "sql": """
SELECT
    order_date AS order_date,
    state,
    sum(revenue) AS total_revenue,
    countDistinct(order_id) AS total_orders
FROM smart_dw.silver_orders_clean
WHERE state != 'Unknown' AND state != ''
GROUP BY order_date, state
ORDER BY total_revenue DESC
""",
        "columns": {
            "order_date": "Date",
            "state": "String",
            "total_revenue": "Float64",
            "total_orders": "UInt64",
        },
    },
}


def get_or_create_database():
    database = db.session.query(Database).filter_by(database_name=DATABASE_NAME).one_or_none()
    if database is None:
        database = Database(database_name=DATABASE_NAME)
        db.session.add(database)
    database.sqlalchemy_uri = DATABASE_URI
    database.expose_in_sqllab = True
    database.allow_run_async = False
    database.allow_ctas = False
    database.allow_cvas = False
    return database


def sync_columns(dataset, columns):
    existing = {column.column_name: column for column in dataset.columns}
    for name, column_type in columns.items():
        column = existing.get(name)
        if column is None:
            column = TableColumn(column_name=name, table=dataset)
            db.session.add(column)
        column.type = column_type
        column.groupby = column_type.lower() in {"string", "date", "datetime"}
        column.filterable = True
        column.is_dttm = column_type.lower() in {"date", "datetime"}


def sync_metrics(dataset, metrics):
    existing = {metric.metric_name: metric for metric in dataset.metrics}
    for metric_name, metric in existing.items():
        if metric_name not in metrics:
            db.session.delete(metric)
    for name, expression in metrics.items():
        metric = existing.get(name)
        if metric is None:
            metric = SqlMetric(metric_name=name, table=dataset)
            db.session.add(metric)
        metric.expression = expression
        metric.warning_text = None


def get_or_create_dataset(database, table_name, columns, sql=None):
    dataset = (
        db.session.query(SqlaTable)
        .filter_by(database_id=database.id, table_name=table_name, schema=SCHEMA)
        .one_or_none()
    )
    if dataset is None:
        dataset = SqlaTable(table_name=table_name, schema=SCHEMA, database=database)
        db.session.add(dataset)
        db.session.flush()

    dataset.sql = sql
    dataset.is_sqllab_view = bool(sql)
    dataset.template_params = "{}"
    dataset.fetch_values_predicate = None
    dataset.main_dttm_col = DATASET_MAIN_DTTS.get(table_name)
    sync_columns(dataset, columns)
    numeric_prefixes = ("int", "uint", "float", "decimal")
    metrics = {"count": "COUNT(*)"}
    for column_name, column_type in columns.items():
        if column_type.lower().startswith(numeric_prefixes):
            metrics[column_name] = f"SUM({column_name})"
    if "order_id" in columns:
        metrics["total_orders"] = "COUNT(DISTINCT order_id)"
    metrics.update(DATASET_CUSTOM_METRICS.get(table_name, {}))
    sync_metrics(dataset, metrics)
    return dataset


def chart_params(dataset, viz_type, **overrides):
    params = {
        "datasource": f"{dataset.id}__table",
        "viz_type": viz_type,
        "adhoc_filters": [],
        "extra_form_data": {},
        "row_limit": 1000,
    }
    params.update(overrides)
    return params


def temporal_filter(column):
    return {
        "clause": "WHERE",
        "subject": column,
        "operator": "TEMPORAL_RANGE",
        "comparator": "No filter",
        "expressionType": "SIMPLE",
    }


def get_latest_month_range():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "superset"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "superset_lokal_kamu"),
        database=SCHEMA,
    )
    result = client.query("SELECT max(order_date) FROM smart_dw.fact_sales")
    max_order_date = result.result_rows[0][0]
    if max_order_date is None:
        return "No filter"
    if hasattr(max_order_date, "date"):
        max_order_date = max_order_date.date()
    month_start = date(max_order_date.year, max_order_date.month, 1)
    month_end = date(max_order_date.year, max_order_date.month, monthrange(max_order_date.year, max_order_date.month)[1])
    return f"{month_start.isoformat()} : {month_end.isoformat()}"


def build_native_time_filter(datasets):
    latest_month_range = get_latest_month_range()
    targets = []
    for dataset_name, column_name in DATASET_MAIN_DTTS.items():
        dataset = datasets.get(dataset_name)
        if dataset is None:
            continue
        targets.append(
            {
                "datasetId": dataset.id,
                "column": {"name": column_name},
            }
        )
    return [
        {
            "id": "NATIVE_FILTER-time_range",
            "controlValues": {
                "enableEmptyFilter": False,
                "defaultToFirstItem": False,
            },
            "name": "Month Filter",
            "filterType": "filter_time",
            "targets": targets,
            "defaultDataMask": {
                "extraFormData": {"time_range": latest_month_range},
                "filterState": {
                    "label": latest_month_range,
                    "validateStatus": False,
                    "value": latest_month_range,
                },
                "ownState": {},
            },
            "cascadeParentIds": [],
            "scope": {
                "rootPath": ["ROOT_ID"],
                "excluded": [],
            },
        }
    ]


def delete_obsolete_charts(desired_chart_names):
    existing_charts = db.session.query(Slice).filter(Slice.slice_name.like(f"{CHART_PREFIX}%")).all()
    for chart in existing_charts:
        if chart.slice_name not in desired_chart_names:
            db.session.delete(chart)


def get_or_create_chart(name, dataset, viz_type, params):
    chart_name = f"{CHART_PREFIX}{name}"
    chart = db.session.query(Slice).filter_by(slice_name=chart_name).one_or_none()
    payload = json.dumps(params)
    if chart is None:
        chart = Slice(slice_name=chart_name, viz_type=viz_type)
        db.session.add(chart)
    chart.datasource_id = dataset.id
    chart.datasource_type = "table"
    chart.viz_type = viz_type
    chart.params = payload
    chart.query_context = None
    return chart


def build_dashboard_layout(charts):
    root_id = "ROOT_ID"
    grid_id = "GRID_ID"
    root_meta = {"background": "BACKGROUND_TRANSPARENT"}
    layout = {
        "DASHBOARD_VERSION_KEY": "v2",
        root_id: {"type": "ROOT", "id": root_id, "children": [grid_id], "meta": root_meta},
        grid_id: {"type": "GRID", "id": grid_id, "children": [], "meta": root_meta},
    }
    row_index = 0
    for chart in charts:
        row_id = f"ROW-{row_index}"
        layout[grid_id]["children"].append(row_id)
        layout[row_id] = {"type": "ROW", "id": row_id, "children": [], "meta": root_meta}
        row_index += 1
        for col_index, chart_item in enumerate(chart):
            if isinstance(chart_item, dict):
                slice_obj = chart_item["slice"]
                width = chart_item.get("width", 6)
                height = chart_item.get("height", 64)
            else:
                slice_obj = chart_item
                width = 3 if len(chart) > 2 else 6
                height = 48 if len(chart) > 2 else 64
            chart_id = f"CHART-{slice_obj.id}"
            meta = {
                "background": "BACKGROUND_TRANSPARENT",
                "chartId": slice_obj.id,
                "height": height,
                "sliceName": slice_obj.slice_name,
                "uuid": str(slice_obj.uuid) if getattr(slice_obj, "uuid", None) else None,
                "width": width,
            }
            layout[row_id]["children"].append(chart_id)
            layout[chart_id] = {
                "type": "CHART",
                "id": chart_id,
                "children": [],
                "meta": meta,
            }
    return layout


def main():
    app = create_app()
    with app.app_context():
        from superset.connectors.sqla.models import SqlaTable, TableColumn, SqlMetric
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        globals()["SqlaTable"] = SqlaTable
        globals()["TableColumn"] = TableColumn
        globals()["SqlMetric"] = SqlMetric
        globals()["Database"] = Database
        globals()["Dashboard"] = Dashboard
        globals()["Slice"] = Slice

        database = get_or_create_database()
        db.session.flush()

        datasets = {}
        for table_name, columns in DATASETS.items():
            datasets[table_name] = get_or_create_dataset(database, table_name, columns)
        for table_name, config in VIRTUAL_DATASETS.items():
            datasets[table_name] = get_or_create_dataset(
                database,
                table_name,
                config["columns"],
                sql=config["sql"].strip(),
            )
        db.session.flush()

        kpi = datasets["fact_sales"]
        forecast = datasets["sales_forecast_ready"]
        forecast_result = datasets["sales_forecast_result"]
        category = datasets["vw_revenue_by_category"]
        sub_category = datasets["vw_revenue_by_sub_category"]
        products = datasets["vw_top_products_by_revenue"]
        channels = datasets["vw_channel_performance"]
        rfm = datasets["vw_customer_segment_distribution"]
        geo = datasets["geographic_daily_summary"]
        kpi_status = datasets["vw_kpi_monthly_status"]
        kpi_daily = datasets["kpi_daily_snapshot"]
        monthly_channels = datasets["channel_monthly_summary"]
        top_states = datasets["vw_top_states_revenue"]

        charts = [
            get_or_create_chart(
                "Total Revenue",
                kpi_daily,
                "big_number_total",
                chart_params(
                    kpi_daily,
                    "big_number_total",
                    metric="total_revenue",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                    time_range="No filter",
                    granularity_sqla="snapshot_date",
                    time_grain_sqla="P1M",
                    compare_lag="1",
                    comparison_type="percentage",
                    show_trend_line=True,
                ),
            ),
            get_or_create_chart(
                "Total Orders",
                kpi_daily,
                "big_number_total",
                chart_params(
                    kpi_daily,
                    "big_number_total",
                    metric="total_orders",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                    time_range="No filter",
                    granularity_sqla="snapshot_date",
                    time_grain_sqla="P1M",
                    compare_lag="1",
                    comparison_type="percentage",
                    show_trend_line=True,
                ),
            ),
            get_or_create_chart(
                "Total Quantity Sold",
                kpi_daily,
                "big_number_total",
                chart_params(
                    kpi_daily,
                    "big_number_total",
                    metric="total_quantity_sold",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                    time_range="No filter",
                    granularity_sqla="snapshot_date",
                    time_grain_sqla="P1M",
                    compare_lag="1",
                    comparison_type="percentage",
                    show_trend_line=True,
                ),
            ),
            get_or_create_chart(
                "Average Order Value",
                kpi_daily,
                "big_number_total",
                chart_params(
                    kpi_daily,
                    "big_number_total",
                    metric="average_order_value",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                    time_range="No filter",
                    granularity_sqla="snapshot_date",
                    time_grain_sqla="P1M",
                    compare_lag="1",
                    comparison_type="percentage",
                    show_trend_line=True,
                ),
            ),
            get_or_create_chart(
                "KPI Performance Status",
                kpi_status,
                "table",
                chart_params(
                    kpi_status,
                    "table",
                    query_mode="raw",
                    all_columns=[
                        "kpi_name",
                        "current_value",
                        "previous_value",
                        "delta_value",
                        "delta_pct",
                        "trend_direction",
                        "minimum_status",
                    ],
                    order_by_cols=[],
                    row_limit=100,
                    server_page_length=10,
                    show_cell_bars=True,
                    color_pn=True,
                    allow_render_html=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Revenue Forecast Ready",
                forecast,
                "echarts_timeseries_line",
                chart_params(
                    forecast,
                    "echarts_timeseries_line",
                    metrics=["total_revenue", "total_orders"],
                    x_axis="sales_date",
                    time_grain_sqla="P1M",
                    x_axis_sort_asc=True,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    adhoc_filters=[],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    seriesType="echarts_timeseries_line",
                    only_total=False,
                    opacity=0.25,
                    markerSize=4,
                    show_legend=True,
                    x_axis_time_format="smart_date",
                    rich_tooltip=True,
                    tooltipTimeFormat="smart_date",
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Revenue Forecast",
                forecast_result,
                "echarts_timeseries_line",
                chart_params(
                    forecast_result,
                    "echarts_timeseries_line",
                    metrics=[
                        {
                            "expressionType": "SQL",
                            "label": "Actual Revenue",
                            "sqlExpression": "SUM(actual_value)",
                        },
                        {
                            "expressionType": "SQL",
                            "label": "Forecast Revenue",
                            "sqlExpression": "SUM(forecast_value)",
                        },
                    ],
                    x_axis="sales_date",
                    time_grain_sqla="P1D",
                    x_axis_sort_asc=True,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    adhoc_filters=[
                        {
                            "clause": "WHERE",
                            "subject": "metric_name",
                            "operator": "==",
                            "comparator": "Revenue",
                            "expressionType": "SIMPLE",
                        }
                    ],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    seriesType="echarts_timeseries_line",
                    only_total=False,
                    opacity=0.25,
                    markerSize=4,
                    show_legend=True,
                    x_axis_time_format="smart_date",
                    rich_tooltip=True,
                    tooltipTimeFormat="smart_date",
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Daily Revenue Trend",
                forecast,
                "echarts_timeseries_line",
                chart_params(
                    forecast,
                    "echarts_timeseries_line",
                    metrics=["total_revenue"],
                    x_axis="sales_date",
                    time_grain_sqla="P1D",
                    x_axis_sort_asc=True,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    adhoc_filters=[],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    seriesType="echarts_timeseries_line",
                    only_total=True,
                    opacity=0.25,
                    markerSize=4,
                    show_legend=False,
                    x_axis_time_format="smart_date",
                    rich_tooltip=True,
                    tooltipTimeFormat="smart_date",
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Daily Orders Trend",
                forecast,
                "echarts_timeseries_line",
                chart_params(
                    forecast,
                    "echarts_timeseries_line",
                    metrics=["total_orders"],
                    x_axis="sales_date",
                    time_grain_sqla="P1D",
                    x_axis_sort_asc=True,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    adhoc_filters=[],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    seriesType="echarts_timeseries_line",
                    only_total=True,
                    opacity=0.25,
                    markerSize=4,
                    show_legend=False,
                    x_axis_time_format="smart_date",
                    rich_tooltip=True,
                    tooltipTimeFormat="smart_date",
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Daily Quantity Trend",
                forecast,
                "echarts_timeseries_line",
                chart_params(
                    forecast,
                    "echarts_timeseries_line",
                    metrics=["total_quantity"],
                    x_axis="sales_date",
                    time_grain_sqla="P1D",
                    x_axis_sort_asc=True,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    adhoc_filters=[],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    seriesType="echarts_timeseries_line",
                    only_total=True,
                    opacity=0.25,
                    markerSize=4,
                    show_legend=False,
                    x_axis_time_format="smart_date",
                    rich_tooltip=True,
                    tooltipTimeFormat="smart_date",
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Revenue by Category",
                category,
                "echarts_timeseries_bar",
                chart_params(
                    category,
                    "echarts_timeseries_bar",
                    x_axis="category",
                    metrics=["total_revenue"],
                    groupby=[],
                    x_axis_sort_asc=False,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    orientation="vertical",
                    x_axis_title_margin=15,
                    y_axis_title_margin=15,
                    y_axis_title_position="Left",
                    sort_series_type="sum",
                    color_scheme="lyftColors",
                    only_total=True,
                    show_legend=False,
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    rich_tooltip=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Revenue by Sub-Category",
                sub_category,
                "echarts_timeseries_bar",
                chart_params(
                    sub_category,
                    "echarts_timeseries_bar",
                    x_axis="sub_category",
                    metrics=["total_revenue"],
                    groupby=[],
                    x_axis_sort_asc=False,
                    x_axis_sort_series="name",
                    x_axis_sort_series_ascending=True,
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    orientation="horizontal",
                    x_axis_title_margin=15,
                    y_axis_title_margin=15,
                    y_axis_title_position="Left",
                    sort_series_type="sum",
                    color_scheme="lyftColors",
                    only_total=True,
                    show_legend=False,
                    y_axis_format="SMART_NUMBER",
                    truncateXAxis=True,
                    y_axis_bounds=[None, None],
                    rich_tooltip=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Monthly Revenue by Channel",
                monthly_channels,
                "echarts_timeseries_bar",
                chart_params(
                    monthly_channels,
                    "echarts_timeseries_bar",
                    x_axis="snapshot_month",
                    groupby=["channel_name"],
                    metrics=["total_revenue"],
                    time_grain_sqla="P1M",
                    row_limit=10000,
                    order_desc=True,
                    show_legend=True,
                    only_total=False,
                    y_axis_format="SMART_NUMBER",
                    rich_tooltip=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Top Products by Revenue",
                products,
                "table",
                chart_params(
                    products,
                    "table",
                    query_mode="aggregate",
                    groupby=["product_name", "category"],
                    metrics=["total_revenue", "total_quantity", "total_orders"],
                    order_by_cols=["[\"total_revenue\", false]"],
                    row_limit=10000,
                    server_page_length=10,
                    table_timestamp_format="smart_date",
                    show_cell_bars=True,
                    color_pn=True,
                    allow_render_html=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Channel Revenue and Orders",
                channels,
                "table",
                chart_params(
                    channels,
                    "table",
                    query_mode="aggregate",
                    groupby=["channel_name", "channel_type"],
                    metrics=["total_revenue", "total_orders"],
                    order_by_cols=["[\"total_revenue\", false]"],
                    row_limit=10000,
                    server_page_length=10,
                    table_timestamp_format="smart_date",
                    show_cell_bars=True,
                    color_pn=True,
                    allow_render_html=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Top States by Revenue",
                top_states,
                "table",
                chart_params(
                    top_states,
                    "table",
                    query_mode="aggregate",
                    groupby=["state"],
                    metrics=["total_revenue", "total_orders"],
                    order_by_cols=["[\"total_revenue\", false]"],
                    row_limit=10000,
                    server_page_length=10,
                    show_cell_bars=True,
                    color_pn=True,
                    allow_render_html=True,
                    time_range="No filter",
                ),
            ),
            get_or_create_chart(
                "Customer Segment Distribution",
                rfm,
                "pie",
                chart_params(
                    rfm,
                    "pie",
                    groupby=["segment_name"],
                    metric="customers",
                    row_limit=1000,
                    sort_by_metric=True,
                    color_scheme="lyftColors",
                    show_labels_threshold=5,
                    show_legend=True,
                    legendType="scroll",
                    legendOrientation="top",
                    label_type="key_value",
                    number_format="SMART_NUMBER",
                    date_format="smart_date",
                    show_labels=True,
                    labels_outside=True,
                    outerRadius=70,
                    innerRadius=45,
                ),
            ),
            get_or_create_chart(
                "Geographic Revenue (India)",
                geo,
                "country_map",
                chart_params(
                    geo,
                    "country_map",
                    select_country="india",
                    entity="iso_code",
                    metric="total_revenue",
                    number_format="SMART_NUMBER",
                    linear_color_scheme="lyftColors",
                    time_range="No filter",
                ),
            ),
        ]
        db.session.flush()
        delete_obsolete_charts({chart.slice_name for chart in charts})

        dashboard = db.session.query(Dashboard).filter_by(dashboard_title=DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE)
            db.session.add(dashboard)
        dashboard.slices = charts
        dashboard.position_json = json.dumps(
            build_dashboard_layout(
                [
                    charts[:4],
                    [
                        {"slice": charts[17], "width": 8, "height": 96},
                        {"slice": charts[14], "width": 4, "height": 72},
                    ],
                    [charts[6], charts[5]],
                    [charts[7], charts[8], charts[9]],
                    [{"slice": charts[4], "width": 12, "height": 96}],
                    [charts[10], charts[11]],
                    [charts[12], charts[13]],
                    [charts[15], charts[16]],
                ]
            )
        )
        dashboard.css = """
.dashboard-component-chart-holder {
  border-radius: 8px;
  box-shadow: 0 1px 8px rgba(25, 35, 60, 0.08);
}
.dashboard-component-tabs,
.dashboard-component-header {
  letter-spacing: 0;
}
"""
        dashboard.json_metadata = json.dumps(
            {
                "label_colors": {},
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "refresh_frequency": 0,
                "native_filter_configuration": build_native_time_filter(datasets),
            }
        )

        db.session.commit()
        print(f"Bootstrapped {DATABASE_NAME} and {DASHBOARD_TITLE}")


if __name__ == "__main__":
    main()
