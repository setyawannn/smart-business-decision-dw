import json
import os
from urllib.parse import quote_plus

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
    },
}

VIRTUAL_DATASETS = {
    "vw_kpi_sales_overview": {
        "sql": """
SELECT
    sum(revenue) AS total_revenue,
    countDistinct(order_id) AS total_orders,
    sum(quantity) AS total_quantity_sold,
    if(countDistinct(order_id) = 0, 0, sum(revenue) / countDistinct(order_id)) AS average_order_value
FROM smart_dw.fact_sales
""",
        "columns": {
            "total_revenue": "Float64",
            "total_orders": "UInt64",
            "total_quantity_sold": "Int64",
            "average_order_value": "Float64",
        },
    },
    "vw_revenue_by_category": {
        "sql": """
SELECT
    ifNull(p.category, 'Unknown') AS category,
    sum(f.revenue) AS total_revenue,
    sum(f.quantity) AS total_quantity
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_product AS p ON f.product_id = p.product_id
GROUP BY category
ORDER BY total_revenue DESC
""",
        "columns": {
            "category": "String",
            "total_revenue": "Float64",
            "total_quantity": "Int64",
        },
    },
    "vw_revenue_by_sub_category": {
        "sql": """
SELECT
    ifNull(p.sub_category, 'Unknown') AS sub_category,
    sum(f.revenue) AS total_revenue,
    sum(f.quantity) AS total_quantity
FROM smart_dw.fact_sales AS f
LEFT JOIN smart_dw.dim_product AS p ON f.product_id = p.product_id
GROUP BY sub_category
ORDER BY total_revenue DESC
LIMIT 20
""",
        "columns": {
            "sub_category": "String",
            "total_revenue": "Float64",
            "total_quantity": "Int64",
        },
    },
    "vw_top_products_by_revenue": {
        "sql": """
SELECT
    ifNull(p.product_name, 'Unknown') AS product_name,
    ifNull(p.category, 'Unknown') AS category,
    s.total_revenue,
    s.total_quantity,
    s.total_orders
FROM smart_dw.product_profitability_summary AS s
LEFT JOIN smart_dw.dim_product AS p ON s.product_id = p.product_id
ORDER BY s.total_revenue DESC
""",
        "columns": {
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
    ifNull(c.channel_name, 'Unknown') AS channel_name,
    ifNull(c.channel_type, 'Unknown') AS channel_type,
    s.total_revenue,
    s.total_orders
FROM smart_dw.channel_performance_summary AS s
LEFT JOIN smart_dw.dim_channel AS c ON s.channel_id = c.channel_id
ORDER BY s.total_revenue DESC
""",
        "columns": {
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
    sync_columns(dataset, columns)
    numeric_prefixes = ("int", "uint", "float", "decimal")
    metrics = {"count": "COUNT(*)"}
    for column_name, column_type in columns.items():
        if column_type.lower().startswith(numeric_prefixes):
            metrics[column_name] = f"SUM({column_name})"
    if "order_id" in columns:
        metrics["total_orders"] = "COUNT(DISTINCT order_id)"
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
        for col_index, slice_obj in enumerate(chart):
            chart_id = f"CHART-{slice_obj.id}"
            meta = {
                "background": "BACKGROUND_TRANSPARENT",
                "chartId": slice_obj.id,
                "height": 48 if len(chart) > 2 else 64,
                "sliceName": slice_obj.slice_name,
                "uuid": str(slice_obj.uuid) if getattr(slice_obj, "uuid", None) else None,
                "width": 3 if len(chart) > 2 else 6,
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

        kpi = datasets["vw_kpi_sales_overview"]
        forecast = datasets["sales_forecast_ready"]
        category = datasets["vw_revenue_by_category"]
        sub_category = datasets["vw_revenue_by_sub_category"]
        products = datasets["vw_top_products_by_revenue"]
        channels = datasets["vw_channel_performance"]
        rfm = datasets["vw_customer_segment_distribution"]

        charts = [
            get_or_create_chart(
                "Total Revenue",
                kpi,
                "big_number_total",
                chart_params(
                    kpi,
                    "big_number_total",
                    metric="total_revenue",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                ),
            ),
            get_or_create_chart(
                "Total Orders",
                kpi,
                "big_number_total",
                chart_params(
                    kpi,
                    "big_number_total",
                    metric="total_orders",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                ),
            ),
            get_or_create_chart(
                "Total Quantity Sold",
                kpi,
                "big_number_total",
                chart_params(
                    kpi,
                    "big_number_total",
                    metric="total_quantity_sold",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
                ),
            ),
            get_or_create_chart(
                "Average Order Value",
                kpi,
                "big_number_total",
                chart_params(
                    kpi,
                    "big_number_total",
                    metric="average_order_value",
                    header_font_size=0.38,
                    subheader_font_size=0.12,
                    y_axis_format="SMART_NUMBER",
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
                    adhoc_filters=[temporal_filter("sales_date")],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    forecastPeriods=10,
                    forecastInterval=0.8,
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
                    adhoc_filters=[temporal_filter("sales_date")],
                    order_desc=True,
                    row_limit=10000,
                    truncate_metric=True,
                    show_empty_columns=True,
                    comparison_type="values",
                    annotation_layers=[],
                    forecastPeriods=10,
                    forecastInterval=0.8,
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
                ),
            ),
            get_or_create_chart(
                "Top Products by Revenue",
                products,
                "table",
                chart_params(
                    products,
                    "table",
                    query_mode="raw",
                    groupby=[],
                    all_columns=["product_name", "category", "total_revenue", "total_quantity", "total_orders"],
                    percent_metrics=[],
                    order_by_cols=[],
                    row_limit=10000,
                    server_page_length=10,
                    table_timestamp_format="smart_date",
                    show_cell_bars=True,
                    color_pn=True,
                    allow_render_html=True,
                ),
            ),
            get_or_create_chart(
                "Channel Revenue and Orders",
                channels,
                "table",
                chart_params(
                    channels,
                    "table",
                    query_mode="raw",
                    groupby=[],
                    all_columns=["channel_name", "channel_type", "total_revenue", "total_orders"],
                    percent_metrics=[],
                    order_by_cols=[],
                    row_limit=10000,
                    server_page_length=10,
                    table_timestamp_format="smart_date",
                    show_cell_bars=True,
                    color_pn=True,
                    allow_render_html=True,
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
        ]
        db.session.flush()

        dashboard = db.session.query(Dashboard).filter_by(dashboard_title=DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE)
            db.session.add(dashboard)
        dashboard.slices = charts
        dashboard.position_json = json.dumps(
            build_dashboard_layout([charts[:4], charts[4:6], charts[6:8], charts[8:10], charts[10:]])
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
            }
        )

        db.session.commit()
        print(f"Bootstrapped {DATABASE_NAME} and {DASHBOARD_TITLE}")


if __name__ == "__main__":
    main()
