import pandas as pd
import clickhouse_connect
from pathlib import Path

DATA_PATH = Path("data/raw/amazon_sale_report.csv")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace(".", "", regex=False)
    )
    return df

def pick_column(df: pd.DataFrame, candidates: list[str], default: str = ""):
    for col in candidates:
        if col in df.columns:
            return df[col].astype(str).fillna(default)
    return pd.Series([default] * len(df))

def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df = normalize_columns(df)

    bronze_df = pd.DataFrame({
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
        "city": pick_column(df, ["city", "ship_city"])
    })

    bronze_df.to_csv("data/raw/temp_bronze.csv", index=False)

    import subprocess
    print("Loading data via docker exec...")
    with open("data/raw/temp_bronze.csv", "rb") as f:
        subprocess.run(
            ["docker", "exec", "-i", "smart_dw_clickhouse", "clickhouse-client", "-q", "INSERT INTO smart_dw.bronze_orders_raw FORMAT CSVWithNames"],
            stdin=f,
            check=True
        )

    print("SUCCESS: data berhasil dimuat ke bronze_orders_raw")
    print(f"Rows loaded: {len(bronze_df)}")

if __name__ == "__main__":
    main()