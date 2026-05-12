# Revisi Database Dashboard Final

Dokumen ini menjelaskan perubahan database yang dipakai untuk menstabilkan dashboard final Superset, mendukung reset dari nol, dan mengaktifkan forecasting visual tanpa bergantung pada runtime forecast bawaan Superset.

## Kenapa Reset Dari Nol Aman

Pipeline project ini memang bersifat rebuild-oriented:

1. `pipeline` menghapus tabel target Bronze/Silver/Gold yang bisa dibangun ulang.
2. `pipeline` memuat ulang dataset sumber dari Kaggle atau file lokal yang sudah tersedia.
3. SQL transform dijalankan ulang dari awal.
4. Superset melakukan bootstrap dataset, chart, dan dashboard lagi sesudah pipeline sukses.

Artinya, perubahan schema yang terdokumentasi di bawah aman dipakai walau environment dibersihkan total lebih dulu.

## Tabel Lama Yang Dipertahankan

- `bronze_orders_raw`
- `silver_orders_clean`
- `fact_sales`
- `dim_customer`
- `dim_product`
- `dim_channel`
- `dim_time`
- `customer_rfm`
- `channel_performance_summary`
- `product_profitability_summary`
- `sales_forecast_ready`
- `geographic_performance_summary`

## Tabel Baru / Direvisi

### `sales_forecast_ready`

Kolom penting:

- `sales_date`
- `total_revenue`
- `total_profit`
- `total_orders`
- `total_quantity`

Grain:

- harian

### `sales_forecast_result`

Kolom penting:

- `sales_date`
- `metric_name`
- `actual_value`
- `forecast_value`
- `lower_bound`
- `upper_bound`
- `model_name`
- `created_at`

Grain:

- harian per metric

Model awal:

- `moving_average_7d`

### `kpi_daily_snapshot`

Kolom:

- `snapshot_date`
- `revenue`
- `orders`
- `quantity`
- `aov`

Grain:

- harian

### `geographic_daily_summary`

Kolom:

- `order_date`
- `iso_code`
- `state`
- `total_revenue`
- `total_orders`

Grain:

- harian per state

Alasan:

- source geo dipindah ke `silver_orders_clean`
- join lewat `dim_customer` tidak stabil karena banyak `customer_id = 'Unknown'`

### `channel_monthly_summary`

Kolom:

- `snapshot_month`
- `channel_name`
- `total_revenue`
- `total_orders`

Grain:

- bulanan per channel

## Kenapa Profit Tidak Dipakai di Chart Utama

Warehouse saat ini memang menyimpan `cost = 0` dan `profit = 0` dari dataset sumber.

Karena itu:

- kolom profit tetap dipertahankan untuk kompatibilitas schema
- chart utama tidak memakai `total_profit` sebagai seri kedua
- seri visual utama diganti ke metric yang bermakna seperti `total_orders`

## Alur Pipeline Baru

1. load raw dataset ke `bronze_orders_raw`
2. transform ke `silver_orders_clean`
3. bangun dimensi dan `fact_sales`
4. bangun analytical tables lama
5. bangun helper table baru:
   - `kpi_daily_snapshot`
   - `geographic_daily_summary`
   - `channel_monthly_summary`
6. bangun `sales_forecast_ready`
7. buat schema `sales_forecast_result`
8. isi `sales_forecast_result` dari pipeline Python
9. validasi row count
10. bootstrap Superset

## Rebuild Lokal Dari Nol

```powershell
$env:CLICKHOUSE_SERVER_PASSWORD='local_clickhouse_password'
docker compose --env-file .env down -v
docker compose --env-file .env up --build -d
```

Yang diharapkan:

- `pipeline` exit sukses
- log `superset` memuat `Bootstrapped Smart DW ClickHouse and Smart Business Decision Dashboard`

## Query Validasi Cepat

### Cek tabel

```sql
SHOW TABLES FROM smart_dw;
```

Harus ada:

- `sales_forecast_ready`
- `sales_forecast_result`
- `kpi_daily_snapshot`
- `geographic_daily_summary`
- `channel_monthly_summary`

### Cek forecast-ready

```sql
DESCRIBE TABLE smart_dw.sales_forecast_ready;
```

Harus ada `total_quantity`.

### Cek KPI harian

```sql
SELECT *
FROM smart_dw.kpi_daily_snapshot
ORDER BY snapshot_date DESC
LIMIT 10;
```

### Cek geo summary

```sql
SELECT countDistinct(state) AS total_states
FROM smart_dw.geographic_daily_summary;
```

Harus lebih dari satu state.

### Cek forecast final

```sql
SELECT metric_name, count() AS rows
FROM smart_dw.sales_forecast_result
GROUP BY metric_name
ORDER BY metric_name;
```

### Cek horizon masa depan

```sql
SELECT
    metric_name,
    countIf(forecast_value IS NOT NULL) AS forecast_rows
FROM smart_dw.sales_forecast_result
GROUP BY metric_name
ORDER BY metric_name;
```

## Dampak Ke Superset

Chart inti sekarang diarahkan ke helper table fisik:

- KPI cards -> `kpi_daily_snapshot`
- map -> `geographic_daily_summary`
- channel bulanan -> `channel_monthly_summary`
- forecast visual -> `sales_forecast_result`

Tujuan:

- chart lebih stabil
- interaksi filter tidak mudah membuat value hilang
- reset dari nol tetap konsisten
