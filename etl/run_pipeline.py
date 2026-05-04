import csv
import os
from datetime import datetime
import shutil
import tempfile
import traceback
from pathlib import Path

import clickhouse_connect
from kaggle.api.kaggle_api_extended import KaggleApi


ROOT_DIR = Path("/app")
DATA_DIR = ROOT_DIR / "data" / "raw"
SQL_DIR = ROOT_DIR / "sql"
DATA_FILE = os.getenv("PIPELINE_INPUT_FILE", "amazon_sale_report.csv")
DATA_PATH = DATA_DIR / DATA_FILE
DOWNLOADS_DIR = ROOT_DIR / "downloads"
LOGS_DIR = ROOT_DIR / "data" / "logs"
PIPELINE_LOG_PATH = LOGS_DIR / "pipeline.log"

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "smart_dw")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_PIPELINE_USER", "pipeline")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PIPELINE_PASSWORD", "pipeline_lokal_kamu")
PIPELINE_DEBUG_KEEPALIVE = os.getenv("PIPELINE_DEBUG_KEEPALIVE", "false").lower() == "true"
PIPELINE_AUTO_DOWNLOAD = os.getenv("PIPELINE_AUTO_DOWNLOAD", "true").lower() == "true"
PIPELINE_FORCE_DOWNLOAD = os.getenv("PIPELINE_FORCE_DOWNLOAD", "false").lower() == "true"
KAGGLE_DATASET = os.getenv(
    "KAGGLE_DATASET",
    "thedevastator/unlock-profits-with-e-commerce-sales-data",
)
KAGGLE_SOURCE_FILENAME = os.getenv("KAGGLE_SOURCE_FILENAME", "Amazon Sale Report.csv")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")

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


def log(message: str) -> None:
    formatted = f"[pipeline] {message}"
    print(formatted, flush=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with PIPELINE_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.utcnow().isoformat()}Z {formatted}\n")


def describe_runtime_context() -> None:
    raw_files = []
    if DATA_DIR.exists():
        raw_files = sorted(path.name for path in DATA_DIR.iterdir())

    log(f"dataset_path={DATA_PATH}")
    log(f"dataset_exists={DATA_PATH.exists()}")
    log(f"raw_directory={DATA_DIR}")
    log(f"raw_directory_exists={DATA_DIR.exists()}")
    log(f"raw_directory_files={raw_files}")
    log(
        "clickhouse_context="
        f"host={CLICKHOUSE_HOST}, port={CLICKHOUSE_PORT}, database={CLICKHOUSE_DB}, user={CLICKHOUSE_USER}"
    )
    log(f"debug_keepalive={PIPELINE_DEBUG_KEEPALIVE}")
    log(f"auto_download={PIPELINE_AUTO_DOWNLOAD}")
    log(f"force_download={PIPELINE_FORCE_DOWNLOAD}")
    log(f"kaggle_dataset={KAGGLE_DATASET}")
    log(f"kaggle_source_filename={KAGGLE_SOURCE_FILENAME}")
    log(f"kaggle_credentials_present={bool(KAGGLE_USERNAME and KAGGLE_KEY)}")


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def find_downloaded_csv(extracted_dir: Path) -> Path:
    preferred = extracted_dir / KAGGLE_SOURCE_FILENAME
    if preferred.exists():
        return preferred

    csv_candidates = sorted(extracted_dir.rglob("*.csv"))
    if not csv_candidates:
        raise FileNotFoundError(
            f"Tidak ada file CSV yang ditemukan setelah ekstraksi dataset Kaggle {KAGGLE_DATASET}"
        )

    normalized_target = DATA_FILE.lower().replace("_", "").replace(" ", "")
    for candidate in csv_candidates:
        normalized_name = candidate.name.lower().replace("_", "").replace(" ", "")
        if normalized_target in normalized_name or "amazonsalereport" in normalized_name:
            return candidate

    return csv_candidates[0]


def download_dataset_from_kaggle() -> None:
    if not KAGGLE_USERNAME or not KAGGLE_KEY:
        raise RuntimeError(
            "KAGGLE_USERNAME atau KAGGLE_KEY belum diisi. "
            "Isi env Kaggle di Coolify agar pipeline bisa mengunduh dataset otomatis."
        )

    ensure_directories()
    log("Starting Kaggle dataset download...")

    with tempfile.TemporaryDirectory(prefix="kaggle-download-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        log("Authenticating with Kaggle API")
        api = KaggleApi()
        api.authenticate()

        log(f"Downloading dataset {KAGGLE_DATASET} to {temp_dir}")
        api.dataset_download_files(
            KAGGLE_DATASET,
            path=str(temp_dir),
            unzip=True,
            force=True,
            quiet=False,
        )

        source_csv = find_downloaded_csv(temp_dir)
        shutil.copy2(source_csv, DATA_PATH)
        log(f"Copied dataset source {source_csv.name} to {DATA_PATH}")


def ensure_dataset_available() -> None:
    ensure_directories()

    if DATA_PATH.exists() and not PIPELINE_FORCE_DOWNLOAD:
        log(f"Using existing dataset at {DATA_PATH}")
        return

    if DATA_PATH.exists() and PIPELINE_FORCE_DOWNLOAD:
        log(f"Force download enabled, replacing existing dataset at {DATA_PATH}")

    if not PIPELINE_AUTO_DOWNLOAD and not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {DATA_PATH}. "
            "Pipeline auto download dimatikan, jadi file harus sudah tersedia."
        )

    download_dataset_from_kaggle()


def normalize_column_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "")


def pick_column(row: dict[str, str], candidates: list[str], default: str = "") -> str:
    for col in candidates:
        if col in row and row[col] not in (None, ""):
            return str(row[col])
    return default


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


def load_bronze_rows() -> list[tuple[str, ...]]:
    ensure_dataset_available()

    try:
        rows = read_csv_rows("utf-8-sig")
    except UnicodeDecodeError:
        log("utf-8-sig decode failed, retrying with latin-1")
        rows = read_csv_rows("latin-1")

    return rows


def read_csv_rows(encoding: str) -> list[tuple[str, ...]]:
    with DATA_PATH.open("r", encoding=encoding, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV tidak memiliki header yang valid: {DATA_PATH}")

        normalized_headers = [normalize_column_name(header) for header in reader.fieldnames]
        log(f"normalized_columns={normalized_headers}")

        bronze_rows: list[tuple[str, ...]] = []
        for raw_row in reader:
            normalized_row = {
                normalize_column_name(str(key)): "" if value is None else str(value).strip()
                for key, value in raw_row.items()
                if key is not None
            }
            bronze_rows.append(
                (
                    pick_column(normalized_row, ["order_id", "orderid", "amazon_order_id", "order"]),
                    pick_column(normalized_row, ["order_date", "date", "order_date_time", "ship_date"]),
                    pick_column(normalized_row, ["customer_id", "buyer_id", "customer"]),
                    pick_column(normalized_row, ["customer_name", "buyer_name", "name"]),
                    pick_column(normalized_row, ["product_id", "sku", "style", "asin"]),
                    pick_column(normalized_row, ["product_name", "item_name", "product"]),
                    pick_column(normalized_row, ["category", "product_category"]),
                    pick_column(normalized_row, ["sub_category", "subcategory", "size"]),
                    pick_column(normalized_row, ["channel", "sales_channel", "platform", "fulfilled_by"]),
                    pick_column(normalized_row, ["quantity", "qty"]),
                    pick_column(normalized_row, ["revenue", "sales", "amount", "total_amount"]),
                    pick_column(normalized_row, ["cost", "cogs", "expense"]),
                    pick_column(normalized_row, ["profit", "gross_profit"]),
                    pick_column(normalized_row, ["discount", "discount_rate"]),
                    pick_column(normalized_row, ["country", "ship_country"]),
                    pick_column(normalized_row, ["state", "ship_state"]),
                    pick_column(normalized_row, ["city", "ship_city"]),
                )
            )
        return bronze_rows


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
    log("Validation results:")
    for row in checks.result_rows:
        log(f"  {row[0]} = {row[1]}")


def validate_clickhouse_connection(client: clickhouse_connect.driver.Client) -> None:
    result = client.query(
        """
        SELECT
            currentDatabase() AS current_database,
            countIf(name = 'smart_dw') AS target_database_exists
        FROM system.databases
        """
    )
    current_database, target_database_exists = result.result_rows[0]
    log(
        "clickhouse_validation="
        f"current_database={current_database}, target_database_exists={target_database_exists}"
    )


def main() -> None:
    describe_runtime_context()
    log("Loading raw Kaggle dataset...")
    bronze_rows = load_bronze_rows()
    log(f"Rows prepared for bronze load: {len(bronze_rows)}")

    log(f"Connecting to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DB}")
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )
    validate_clickhouse_connection(client)

    log("Refreshing target tables...")
    for statement in REFRESH_STATEMENTS:
        client.command(statement)

    log("Creating warehouse objects...")
    for sql_file in PIPELINE_SQL_FILES:
        if sql_file.name == "create_bronze_tables.sql":
            log(f"Running SQL file: {sql_file}")
            run_sql_file(client, sql_file)
            break

    log("Inserting bronze data...")
    client.insert(
        "smart_dw.bronze_orders_raw",
        bronze_rows,
        column_names=[
            "order_id",
            "order_date",
            "customer_id",
            "customer_name",
            "product_id",
            "product_name",
            "category",
            "sub_category",
            "channel_name",
            "quantity",
            "revenue",
            "cost",
            "profit",
            "discount",
            "country",
            "state",
            "city",
        ],
    )

    log("Running Silver and Gold transformations...")
    for sql_file in PIPELINE_SQL_FILES[1:]:
        log(f"Running SQL file: {sql_file}")
        run_sql_file(client, sql_file)

    validate(client)
    log("Pipeline completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"Pipeline failed: {exc}")
        stack_trace = traceback.format_exc()
        print(stack_trace, flush=True)
        with PIPELINE_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(stack_trace)
        raise
