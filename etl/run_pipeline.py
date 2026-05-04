import os
from pathlib import Path

import clickhouse_connect
import pandas as pd


ROOT_DIR = Path("/app")
DATA_DIR = ROOT_DIR / "data" / "raw"
SQL_DIR = ROOT_DIR / "sql"
DATA_FILE = os.getenv("PIPELINE_INPUT_FILE", "amazon_sale_report.csv")
DATA_PATH = DATA_DIR / DATA_FILE

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "smart_dw")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_SERVER_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_SERVER_PASSWORD", "")

PIPELINE_SQL_FILES = [
    SQL_DIR / "bronze" / "create_bronze_tables.sql",
    SQL_DIR / "silver" / "transform_silver_orders.sql",
    SQL_DIR / "gold" / "create_dimensions.sql",
    SQL_DIR / "gold" / "create_fact_sales.sql",
    SQL_DIR / "gold" / "create_analytical_tables.sql",
]

REFRESH_STATEMENTS = [
    "TRUNCATE TABLE IF EXISTS smart_dw.bronze_orders_raw",
    "DROP TABLE IF EXISTS smart_dw.silver_orders_clean",
    "DROP TABLE IF EXISTS smart_dw.fact_sales",
    "DROP TABLE IF EXISTS smart_dw.dim_customer",
    "DROP TABLE IF EXISTS smart_dw.dim_product",
    "DROP TABLE IF EXISTS smart_dw.dim_channel",
    "DROP TABLE IF EXISTS smart_dw.dim_time",
    "DROP TABLE IF EXISTS smart_dw.customer_rfm",
    "DROP TABLE IF EXISTS smart_dw.channel_performance_summary",
    "DROP TABLE IF EXISTS smart_dw.product_profitability_summary",
    "DROP TABLE IF EXISTS smart_dw.sales_forecast_ready",
    "DROP TABLE IF EXISTS smart_dw.geographic_performance_summary",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace(".", "", regex=False)
    )
    return df


def pick_column(df: pd.DataFrame, candidates: list[str], default: str = "") -> pd.Series:
    for col in candidates:
        if col in df.columns:
            return df[col].astype(str).fillna(default)
    return pd.Series([default] * len(df))


def split_sql(sql: str) -> list[str]:
    statements = []
    current = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    trailing = "\n".join(current).strip().rstrip(";").strip()
    if trailing:
        statements.append(trailing)
    return statements


def run_sql_file(client: clickhouse_connect.driver.Client, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    for statement in split_sql(sql):
        client.command(statement)


def load_bronze_dataframe() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {DATA_PATH}. "
            "Pastikan file Kaggle sudah diletakkan pada data/raw/amazon_sale_report.csv"
        )

    df = pd.read_csv(DATA_PATH)
    df = normalize_columns(df)

    bronze_df = pd.DataFrame(
        {
            "order_id": pick_column(df, ["order_id", "orderid", "amazon_order_id", "order"]),
            "order_date": pick_column(df, ["order_date", "date", "order_date_time", "ship_date"]),
            "customer_id": pick_column(df, ["customer_id", "buyer_id", "customer"]),
            "customer_name": pick_column(df, ["customer_name", "buyer_name", "name"]),
            "product_id": pick_column(df, ["product_id", "sku", "style", "asin"]),
            "product_name": pick_column(df, ["product_name", "item_name", "product"]),
            "category": pick_column(df, ["category", "product_category"]),
            "sub_category": pick_column(df, ["sub_category", "subcategory", "size"]),
            "channel_name": pick_column(df, ["channel", "sales_channel", "platform", "fulfilled_by"]),
            "quantity": pick_column(df, ["quantity", "qty"]),
            "revenue": pick_column(df, ["revenue", "sales", "amount", "total_amount"]),
            "cost": pick_column(df, ["cost", "cogs", "expense"]),
            "profit": pick_column(df, ["profit", "gross_profit"]),
            "discount": pick_column(df, ["discount", "discount_rate"]),
            "country": pick_column(df, ["country", "ship_country"]),
            "state": pick_column(df, ["state", "ship_state"]),
            "city": pick_column(df, ["city", "ship_city"]),
        }
    )
    return bronze_df


def validate(client: clickhouse_connect.driver.Client) -> None:
    checks = client.query(
        """
        SELECT 'bronze_rows' AS check_name, count() AS value FROM smart_dw.bronze_orders_raw
        UNION ALL
        SELECT 'silver_rows' AS check_name, count() AS value FROM smart_dw.silver_orders_clean
        UNION ALL
        SELECT 'fact_sales_rows' AS check_name, count() AS value FROM smart_dw.fact_sales
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
        WHERE revenue < 0
        """
    )
    print("Validation results:")
    for row in checks.result_rows:
        print(f"  {row[0]} = {row[1]}")


def main() -> None:
    print(f"Connecting to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DB}")
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )

    print("Loading raw Kaggle dataset...")
    bronze_df = load_bronze_dataframe()
    print(f"Rows prepared for bronze load: {len(bronze_df)}")

    print("Refreshing target tables...")
    for statement in REFRESH_STATEMENTS:
        client.command(statement)

    print("Creating warehouse objects...")
    for sql_file in PIPELINE_SQL_FILES:
        if sql_file.name == "create_bronze_tables.sql":
            run_sql_file(client, sql_file)
            break

    print("Inserting bronze data...")
    client.insert_df("smart_dw.bronze_orders_raw", bronze_df)

    print("Running Silver and Gold transformations...")
    for sql_file in PIPELINE_SQL_FILES[1:]:
        run_sql_file(client, sql_file)

    validate(client)
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
