<div align="center">

# 🏢 Smart Business Decision Data Warehouse

**Implementasi Data Warehouse berbasis Medallion Architecture untuk Analisis E-Commerce Multi-Channel**

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?style=flat-square&logo=clickhouse&logoColor=black)](https://clickhouse.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat-square&logo=mysql&logoColor=white)]()
[![Status](https://img.shields.io/badge/Status-Completed-brightgreen?style=flat-square)]()

</div>

---

## 📋 Daftar Isi

- [🏢 Smart Business Decision Data Warehouse](#-smart-business-decision-data-warehouse)
  - [📋 Daftar Isi](#-daftar-isi)
  - [🎯 Overview](#-overview)
    - [Pipeline Utama](#pipeline-utama)
    - [Ruang Lingkup Proyek](#ruang-lingkup-proyek)
  - [📊 Tech Stack](#-tech-stack)
  - [🏗️ Arsitektur Data](#️-arsitektur-data)
    - [Medallion Architecture](#medallion-architecture)
      - [1️⃣ Bronze Layer — Raw Data](#1️⃣-bronze-layer--raw-data)
      - [2️⃣ Silver Layer — Clean Data](#2️⃣-silver-layer--clean-data)
      - [3️⃣ Gold Layer — Business Ready](#3️⃣-gold-layer--business-ready)
    - [Star Schema](#star-schema)
  - [🗃️ Dataset](#️-dataset)
    - [Sumber Dataset](#sumber-dataset)
    - [Struktur Folder Dataset](#struktur-folder-dataset)
  - [📁 Struktur Repository](#-struktur-repository)
  - [🚀 Instalasi dan Setup](#-instalasi-dan-setup)
    - [Prasyarat](#prasyarat)
    - [Langkah Instalasi Umum](#langkah-instalasi-umum)
      - [1. Clone Repository \& Setup Dataset](#1-clone-repository--setup-dataset)
      - [2. Buat Environment dan Install Dependensi](#2-buat-environment-dan-install-dependensi)
      - [3. Jalankan Docker Environment Terpadu](#3-jalankan-docker-environment-terpadu)
  - [⚙️ Menjalankan Pipeline dari Data Mentah Hingga Dashboard](#️-menjalankan-pipeline-dari-data-mentah-hingga-dashboard)
    - [🎉 Mengakses Dashboard](#-mengakses-dashboard)
  - [📈 Output yang Diharapkan](#-output-yang-diharapkan)
  - [🔍 Validasi Data](#-validasi-data)
  - [📊 Analisis dan Tabel Analitik](#-analisis-dan-tabel-analitik)
    - [RFM Analysis](#rfm-analysis)
    - [Channel Performance](#channel-performance)
    - [Product Profitability](#product-profitability)
    - [Sales Forecasting](#sales-forecasting)
  - [🛠️ Perintah Berguna](#️-perintah-berguna)
    - [📸 Dokumentasi Laporan](#-dokumentasi-laporan)
  - [📝 Catatan Penting](#-catatan-penting)
    - [Keterbatasan Dataset](#keterbatasan-dataset)
    - [Catatan Teknis](#catatan-teknis)
      - [🔧 Format Tanggal](#-format-tanggal)
      - [🔧 Alias Conflict](#-alias-conflict)
  - [🧹 Reset Environment](#-reset-environment)
    - [Menghentikan Container](#menghentikan-container)
    - [Reset Total (Hapus Data)](#reset-total-hapus-data)
  - [� Status Proyek](#-status-proyek)
  - [🔮 Pengembangan Selanjutnya](#-pengembangan-selanjutnya)
  - [👤 Author](#-author)

---

## 🎯 Overview

**Smart Business Decision Data Warehouse** adalah proyek implementasi Data Warehouse yang menggunakan pendekatan **Medallion Architecture** untuk studi kasus **E-Commerce Multi-Channel Sales Dataset**. Proyek ini bertujuan membangun repositori data yang terstruktur dari data mentah hingga data siap analisis.

### Pipeline Utama

```text
┌─────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  CSV Dataset │────▶│  Python ETL  │────▶│ ClickHouse Data      │
│  (Kaggle)    │     │  (Pandas)    │     │ Warehouse            │
└─────────────┘     └──────────────┘     └──────────────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
           ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
           │ Bronze Layer │───────────▶│ Silver Layer │───────────▶│  Gold Layer  │
           │  (Raw Data)  │            │(Clean Data)  │            │(Star Schema) │
           └──────────────┘            └──────────────┘            └──────────────┘
                                                                           │
                                                                           ▼
                                                                  ┌──────────────┐
                                                                  │  Analytical  │
                                                                  │   Tables     │
                                                                  └──────────────┘
```

### Ruang Lingkup Proyek

| In Scope ✅ | Out of Scope ❌ |
|------------|----------------|
| Environment lokal dengan Docker | Dashboard visualisasi |
| ClickHouse sebagai Data Warehouse | Visualisasi interaktif |
| Ingestion data CSV ke Bronze Layer | Forecasting model final |
| Cleaning & standardisasi Silver Layer | Deployment production |
| Star Schema pada Gold Layer | |
| Analytical tables untuk analitik lanjutan | |
| Validasi pipeline data warehouse | |

> **Catatan:** Tahap dashboard dan visualisasi akan dilakukan pada fase berikutnya menggunakan data dari Gold Layer.

---

## 📊 Tech Stack

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| **Containerization** | Docker | Menjalankan environment lokal |
| **Data Warehouse** | ClickHouse | Menyimpan dan memproses data analitik |
| **ETL Engine** | Python + Pandas | Membaca CSV dan load data ke Bronze Layer |
| **Data Processing** | SQL | Transformasi Bronze → Silver → Gold |
| **Documentation** | Markdown | Dokumentasi proyek |
| **Dataset Source** | Kaggle | Sumber data e-commerce multi-channel |

---

## 🏗️ Arsitektur Data

### Medallion Architecture

Proyek ini menggunakan pendekatan **Medallion Architecture** yang terdiri dari tiga layer utama:

#### 1️⃣ Bronze Layer — Raw Data

Layer ini menyimpan data mentah dari file CSV mendekati bentuk aslinya.

**Tabel:** `bronze_orders_raw`

**Karakteristik:**
- Data masih mentah tanpa transformasi bisnis kompleks
- Sebagian besar kolom bertipe `String`
- Menyimpan seluruh kolom dari dataset sumber
- Digunakan sebagai raw repository untuk reprocessing
- Dilengkapi `ingestion_time` untuk tracking

**Engine:** `MergeTree` dengan `ORDER BY (order_id)`

#### 2️⃣ Silver Layer — Clean Data

Layer ini berisi data yang sudah dibersihkan, distandarisasi, dan divalidasi.

**Tabel:** `silver_orders_clean`

**Transformasi yang Dilakukan:**

| Aspek | Transformasi | Contoh |
|-------|-------------|--------|
| **Tanggal** | Konversi `MM-DD-YY` → `Date` | `06-07-22` → `2022-06-07` |
| **Quantity** | String → `Int32` | `"2"` → `2` |
| **Revenue** | String → `Float64` | `"125.50"` → `125.50` |
| **Validasi** | Pembersihan nilai tidak valid | Quantity > 0, Revenue ≥ 0 |
| **Null Handling** | Nilai kosong → default | `Unknown` untuk ID/Nama |

**Engine:** `MergeTree` dengan `ORDER BY (order_date, order_id)`

#### 3️⃣ Gold Layer — Business Ready

Layer ini berisi data siap analisis dengan model **Star Schema** dan tabel analitik.

### Star Schema

```text
                    ┌─────────────────┐
                    │   dim_time      │
                    │  (Waktu)        │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  dim_customer │   │  fact_sales   │   │  dim_product  │
│  (Pelanggan)  │   │  (Fakta)      │   │  (Produk)     │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  dim_channel  │
                    │  (Channel)    │
                    └───────────────┘
```

**Fact Table:**

| Tabel | Deskripsi | Engine |
|-------|-----------|--------|
| `fact_sales` | Tabel fakta transaksi penjualan | MergeTree, Partition by `toYYYYMM(order_date)` |

**Dimension Tables:**

| Tabel | Deskripsi | Kolom Kunci |
|-------|-----------|-------------|
| `dim_customer` | Dimensi pelanggan | `customer_id`, `customer_name`, `country` |
| `dim_product` | Dimensi produk | `product_id`, `category`, `unit_price` |
| `dim_channel` | Dimensi channel penjualan | `channel_id`, `channel_name`, `channel_type` |
| `dim_time` | Dimensi waktu | `date`, `day`, `month`, `quarter`, `year` |

**Analytical Tables:**

| Tabel | Deskripsi | Use Case |
|-------|-----------|----------|
| `customer_rfm` | RFM Analysis (Recency, Frequency, Monetary) | Segmentasi pelanggan |
| `channel_performance_summary` | Ringkasan performa channel | Analisis channel |
| `product_profitability_summary` | Ringkasan profitabilitas produk | Analisis produk |
| `sales_forecast_ready` | Data siap forecasting | Time series analysis |

---

## 🗃️ Dataset

### Sumber Dataset

**E-Commerce Multi-Channel Sales Dataset**

- **Source:** [Kaggle — Unlock Profits with E-Commerce Sales Data](https://www.kaggle.com/datasets/thedevastator/unlock-profits-with-e-commerce-sales-data)
- **File Utama:** `amazon_sale_report.csv`

### Struktur Folder Dataset

Dataset mentah tidak disimpan langsung di repository GitHub karena ukuran file cukup besar. Silakan download dataset secara manual dari Kaggle.

```
data/
└── raw/
    ├── amazon_sale_report.csv      ← File wajib untuk pipeline utama
    ├── sale_report.csv
    ├── international_sale_report.csv
    ├── may_2022.csv
    ├── expense_iigf.csv
    ├── p_l_march_2021.csv
    └── cloud_warehouse_compersion_chart.csv
```

> **Penting:** Untuk implementasi utama, file yang wajib tersedia adalah **`data/raw/amazon_sale_report.csv`**.

**Tips Penamaan File:**
Jika nama file dari Kaggle masih menggunakan spasi, ubah menjadi lowercase dengan underscore:
```
Amazon Sale Report.csv  →  amazon_sale_report.csv
```

---

## 📁 Struktur Repository

```
smart-business-decision-dw/
│
├── 📂 data/
│   └── 📂 raw/                       # Folder dataset mentah
│       ├── .gitkeep
│       └── README.md
│
├── 📂 etl/
│   └── load_to_clickhouse.py         # Script ETL Python
│
├── 📂 sql/
│   ├── 📂 bronze/
│   │   └── create_bronze_tables.sql  # DDL Bronze Layer
│   │
│   ├── 📂 silver/
│   │   └── transform_silver_orders.sql  # Transformasi ke Silver
│   │
│   ├── 📂 gold/
│   │   ├── create_dimensions.sql     # DDL Dimension Tables
│   │   ├── create_fact_sales.sql     # DDL Fact Table
│   │   └── create_analytical_tables.sql  # DDL Analytical Tables
│   │
│   └── 📂 validation/
│       └── data_quality_checks.sql   # Validasi data quality
│
├── 📂 docs/
│   └── 📂 diagrams/
│       ├── data_dictionary.md
│       └── implementation_report.md
│
├── 📂 screenshots/                   # Dokumentasi visual
│
├── docker-compose.yml                # Konfigurasi Docker
├── requirements.txt                  # Dependensi Python
├── .gitignore                        # Konfigurasi Git ignore
└── README.md                         # Dokumentasi ini
```

---

## 🚀 Instalasi dan Setup

### Prasyarat

Pastikan perangkat sudah memiliki:

| Prasyarat | Versi Minimal | Cek Versi |
|-----------|--------------|-----------|
| Git | Terbaru | `git --version` |
| Docker Desktop | Terbaru | `docker --version` |
| Python | 3.10+ | `python --version` |

### Langkah Instalasi Umum

#### 1. Clone Repository & Setup Dataset
```bash
git clone https://github.com/setyawannn/smart-business-decision-dw.git
cd smart-business-decision-dw
```

Bagi Anda yang baru pertama melakukan setup, unduh data mentah secara otomatis menggunakan script utilitas (Kaggle CLI yang telah ditautkan pada API `~/.kaggle/kaggle.json` sangat diperlukan sebelum menjalankan script ini):
```bash
bash scripts/download_dataset.sh
```
*(Script ini akan mengunduh, mengekstrak, dan merename file `Amazon Sale Report.csv` menjadi `amazon_sale_report.csv` yang diproses ETL ini).*

#### 2. Buat Environment dan Install Dependensi
```bash
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 3. Jalankan Docker Environment Terpadu
Proyek ini memuat **ClickHouse** (layanan database warehouse) dan **Superset** (layanan dashboard) dalam satu ekosistem.
```bash
docker compose up -d
```
Tunggu sekitar 2-3 menit hingga inisialisasi awal Superset di dalam kontainer selesai.
Pastikan semuanya berjalan (opsional cek status container):
```bash
docker ps
```

---

## 🚀 Deployment dengan Coolify (Production)

Arsitektur aplikasi ini (*ClickHouse + Apache Superset*) sudah disiapkan untuk deploy sekali jalan di **Coolify** memakai Docker Compose. `docker-compose.yml` menjadi sumber konfigurasi utama: ClickHouse berjalan internal, service `pipeline` menjalankan download Kaggle dan ETL otomatis, lalu Superset melakukan bootstrap dashboard.

**1. Konfigurasi Repositori Git**
* Tambahkan Repositori ini ke *Coolify Applications* dengan metode **"Docker Compose"**.
* Konfigurasi Branch ke komit terbaru Anda (`main`).
* Pastikan compose file yang dipakai adalah `docker-compose.yml`.

**2. Konfigurasi Environment Variables**
Masukkan environment variable berikut pada GUI Coolify. Kaggle credential cukup lewat env; tidak perlu upload `kaggle.json` atau menjalankan pre-deployment command manual.
```ini
SUPERSET_SECRET_KEY=change_this_with_a_long_random_secret
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=change_this_admin_password
SUPERSET_ADMIN_EMAIL=admin@example.com
SUPERSET_ADMIN_FIRSTNAME=Smart
SUPERSET_ADMIN_LASTNAME=DW
SUPERSET_PORT=8088

CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_DATABASE=smart_dw
CLICKHOUSE_SERVER_USER=default
CLICKHOUSE_SERVER_PASSWORD=change_this_clickhouse_admin_password
CLICKHOUSE_USER=superset
CLICKHOUSE_PASSWORD=change_this_superset_password

PIPELINE_INPUT_FILE=amazon_sale_report.csv
PIPELINE_DEBUG_KEEPALIVE=false
PIPELINE_AUTO_DOWNLOAD=true
PIPELINE_FORCE_DOWNLOAD=false
KAGGLE_DATASET=thedevastator/unlock-profits-with-e-commerce-sales-data
KAGGLE_SOURCE_FILENAME=Amazon Sale Report.csv
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key
```

**3. Deploy dan Networking**
* Klik `Deploy`. Urutan otomatisnya: `clickhouse` healthy -> `pipeline` sukses -> `superset` start.
* Arahkan domain Coolify ke service `superset` dengan container port `8088`.
* ClickHouse tidak perlu diekspos public; service lain mengaksesnya lewat network internal Docker Compose.
* Tunggu hingga log `pipeline` berisi `Pipeline completed successfully` dan log `superset` berisi `[superset-start] Starting Superset web server on 0.0.0.0:8088`.

---

## ⚙️ Menjalankan Pipeline dari Data Mentah Hingga Dashboard

Tidak perlu menjalankan `docker exec` satu per satu. Semua tahap pipeline sudah diorkestrasi oleh service `pipeline` dan bootstrap Superset.

```bash
docker compose up -d --build
```

Urutan otomatis:

1. ClickHouse start dan healthcheck siap.
2. Dataset Kaggle diunduh ke volume `shared_data`.
3. CSV utama disalin sebagai `/app/data/raw/amazon_sale_report.csv`.
4. Bronze, Silver, Gold, dan tabel analitik dibuat ulang.
5. Validasi data berjalan dan ditulis ke log pipeline.
6. Superset membuat admin, koneksi ClickHouse, dataset, chart, dan dashboard.


### 🎉 Mengakses Dashboard
Setelah log Superset menampilkan bootstrap berhasil, buka browser Anda:

- **Akses URL:** [http://localhost:8088](http://localhost:8088)
- **Login:**
  - Username: `admin`
  - Password: sesuai `SUPERSET_ADMIN_PASSWORD`

Klik menu **Dashboards** > lalu buka **Smart Business Decision Dashboard**. Anda akan melihat data hasil warehouse Anda divisualisasikan dengan apik!

---

## 📈 Output yang Diharapkan

Setelah seluruh pipeline berhasil dijalankan, tabel berikut akan tersedia di database `smart_dw`:

```sql
docker exec -it smart_dw_clickhouse clickhouse-client --query "SHOW TABLES FROM smart_dw"
```

**Expected Output:**

```
bronze_orders_raw
channel_performance_summary
channel_monthly_summary
customer_rfm
dim_channel
dim_customer
dim_product
dim_time
fact_sales
geographic_daily_summary
kpi_daily_snapshot
product_profitability_summary
sales_forecast_result
sales_forecast_ready
silver_orders_clean
```

---

## 🔍 Validasi Data

Script `sql/validation/data_quality_checks.sql` melakukan pengecekan kualitas data pada setiap layer.

**Contoh Hasil Validasi:**

| Check Name | Hasil | Penjelasan |
|-----------|-------|-----------|
| `bronze_rows` | 128.975 | Jumlah data mentah yang berhasil dimuat |
| `silver_rows` | 116.168 | Jumlah data valid setelah cleaning |
| `fact_sales_rows` | 116.168 | Jumlah data pada tabel fakta |
| `null_order_id_in_silver` | 0 | Tidak ada order ID kosong ✅ |
| `invalid_quantity_in_silver` | 0 | Tidak ada quantity tidak valid ✅ |
| `negative_revenue_in_silver` | 0 | Tidak ada revenue negatif ✅ |

**Interpretasi:**
- Selisih antara Bronze dan Silver (12.807 rows) menunjukkan data yang dibersihkan (duplikat, format tidak valid, nilai null, dll.)
- **0 error** pada validasi menunjukkan kualitas data Silver sudah baik

---

## 📊 Analisis dan Tabel Analitik

### RFM Analysis

Tabel `customer_rfm` mengimplementasikan **RFM Analysis** untuk segmentasi pelanggan:

| Metric | Definisi | Formula |
|--------|----------|---------|
| **Recency (R)** | Seberapa baru pelanggan bertransaksi | `dateDiff('day', last_order_date, max_date)` |
| **Frequency (F)** | Seberapa sering bertransaksi | `countDistinct(order_id)` |
| **Monetary (M)** | Total nilai transaksi | `sum(revenue)` |

**Segmentasi Pelanggan:**

| Segment | Kriteria | Strategi |
|---------|----------|----------|
| **Champions** | Recency ≤ 30 hari, Frequency ≥ 5, Monetary ≥ 1000 | Reward & loyalitas |
| **Loyal** | Recency ≤ 60 hari, Frequency ≥ 3 | Upselling |
| **At Risk** | Recency > 90 hari, Monetary ≥ 500 | Re-engagement |
| **Hibernating** | Recency > 120 hari | Win-back campaign |
| **Regular** | Selain kriteria di atas | Maintain engagement |

### Channel Performance

Tabel `channel_performance_summary` menyediakan ringkasan performa setiap channel:

| Metrik | Deskripsi |
|--------|-----------|
| `total_revenue` | Total pendapatan per channel |
| `total_profit` | Total profit per channel |
| `total_orders` | Jumlah unik order per channel |
| `profit_margin` | Rasio profit terhadap revenue |

### Product Profitability

Tabel `product_profitability_summary` menganalisis profitabilitas produk:

| Metrik | Deskripsi |
|--------|-----------|
| `total_revenue` | Total pendapatan per produk |
| `total_profit` | Total profit per produk |
| `total_quantity` | Total quantity terjual |
| `total_orders` | Jumlah unik order |
| `profit_margin` | Margin profit per produk |

### Sales Forecasting

Tabel `sales_forecast_ready` menyediakan data agregasi harian yang siap digunakan untuk analisis time series dan forecasting:

| Kolom | Deskripsi |
|-------|-----------|
| `sales_date` | Tanggal transaksi |
| `total_revenue` | Total revenue harian |
| `total_profit` | Total profit harian |
| `total_orders` | Total order harian |
| `total_quantity` | Total quantity harian |

### Forecast Result

Tabel `sales_forecast_result` menyimpan hasil forecasting final:

| Kolom | Deskripsi |
|-------|-----------|
| `sales_date` | Tanggal historis atau horizon forecast |
| `metric_name` | Nama metric forecast |
| `actual_value` | Nilai aktual historis |
| `forecast_value` | Nilai prediksi |
| `lower_bound` | Batas bawah prediksi |
| `upper_bound` | Batas atas prediksi |
| `model_name` | Nama model baseline |

### Helper Tables Dashboard

Pipeline juga membangun tabel ringkas berikut:

| Tabel | Grain | Kegunaan |
|------|-------|----------|
| `kpi_daily_snapshot` | Harian | KPI cards + trendline |
| `geographic_daily_summary` | Harian per state | Map revenue India |
| `channel_monthly_summary` | Bulanan per channel | Chart channel bulanan |

---

## 🛠️ Perintah Berguna

Berikut adalah perintah-perintah yang dapat digunakan untuk dokumentasi dan eksplorasi data:

### 📸 Dokumentasi Laporan

| Gambar | Perintah |
|--------|----------|
| **5.1** Container berjalan | `docker ps --filter "name=smart_dw_clickhouse"` |
| **5.2** Daftar tabel | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SHOW TABLES FROM smart_dw"` |
| **5.3** Struktur Bronze | `docker exec -it smart_dw_clickhouse clickhouse-client --query "DESCRIBE TABLE smart_dw.bronze_orders_raw"` |
| **5.4** Struktur Silver | `docker exec -it smart_dw_clickhouse clickhouse-client --query "DESCRIBE TABLE smart_dw.silver_orders_clean"` |
| **5.5** Sample Silver | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT order_id, order_date, product_id, category, sub_category, channel_name, quantity, revenue, country FROM smart_dw.silver_orders_clean LIMIT 10"` |
| **5.6** Struktur Fact Sales | `docker exec -it smart_dw_clickhouse clickhouse-client --query "DESCRIBE TABLE smart_dw.fact_sales"` |
| **5.7** Hasil validasi | `docker exec -it smart_dw_clickhouse clickhouse-client --queries-file /sql/validation/data_quality_checks.sql` |
| **5.8** Sample Customer RFM | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT customer_id, recency, frequency, monetary, segment_name FROM smart_dw.customer_rfm LIMIT 10"` |
| **5.9** Sample Channel Performance | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT * FROM smart_dw.channel_performance_summary LIMIT 10"` |
| **5.10** Sample Product Performance | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT * FROM smart_dw.product_profitability_summary ORDER BY total_revenue DESC LIMIT 10"` |
| **5.11** Sample Forecast Ready | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT * FROM smart_dw.sales_forecast_ready ORDER BY sales_date LIMIT 10"` |
| **5.12** Sample Forecast Result | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT * FROM smart_dw.sales_forecast_result ORDER BY metric_name, sales_date LIMIT 10"` |
| **5.13** Sample KPI Daily Snapshot | `docker exec -it smart_dw_clickhouse clickhouse-client --query "SELECT * FROM smart_dw.kpi_daily_snapshot ORDER BY snapshot_date DESC LIMIT 10"` |

---

## 📝 Catatan Penting

### Keterbatasan Dataset

File utama `amazon_sale_report.csv` memiliki keterbatasan pada beberapa atribut penting:

| Atribut | Status | Penanganan |
|---------|--------|------------|
| `customer_id` | Tidak lengkap | Diisi `Unknown` |
| `customer_name` | Tidak lengkap | Diisi `Unknown` |
| `product_name` | Tidak lengkap | Menggunakan `product_id` |
| `cost` | Tidak tersedia | Kolom tersedia, nilai 0 |
| `profit` | Tidak tersedia | Kolom tersedia, nilai 0 |
| `discount` | Tidak tersedia | Kolom tersedia, nilai 0 |

**Dampak:** Analisis utama difokuskan pada `revenue`, `quantity`, `product`, `category`, `channel`, dan `time`.

**Catatan tambahan:** kolom `cost` dan `profit` tetap dipertahankan di schema warehouse untuk kompatibilitas, tetapi dashboard utama tidak memakai seri profit sebagai indikator utama karena sumber data mengisinya dengan nol.

### Catatan Teknis

#### 🔧 Format Tanggal

Dataset menggunakan format tanggal **MM-DD-YY** yang dikonversi ke **YYYY-MM-DD**:

```
Input:  06-07-22
Output: 2022-06-07
```

Implementasi menggunakan `substring` dan `concat` untuk parsing manual:

```sql
toDate(concat('20', raw_yy, '-', raw_mm, '-', raw_dd)) AS order_date
```

#### 🔧 Alias Conflict

Penggunaan alias yang sama dengan nama kolom asli menyebabkan konflik tipe data. **Solusi:** Semua kolom dari Bronze Layer diberi prefix `raw_` di subquery.

| Sebelum | Sesudah |
|---------|---------|
| `order_date` | `raw_order_date` → `order_date` |
| `quantity` | `raw_quantity` → `quantity` |
| `revenue` | `raw_revenue` → `revenue` |

Pendekatan ini membuat transformasi lebih stabil dan menghindari konflik tipe data pada ClickHouse.

---

## 🧹 Reset Environment

### Menghentikan Container

```bash
docker compose down
```

### Reset Total (Hapus Data)

> ⚠️ **Peringatan:** Perintah ini akan menghapus seluruh data ClickHouse yang tersimpan!

```bash
docker compose down -v
```

Gunakan hanya jika ingin memulai dari awal.

---

## � Status Proyek

| Komponen | Status |
|----------|--------|
| Docker Environment | ✅ Completed |
| ClickHouse Setup | ✅ Completed |
| Medallion ETL/ELT Pipeline | ✅ Completed |
| Data Quality Validation | ✅ Completed |
| Data Analytics (RFM) | ✅ Completed |
| **Apache Superset Setup** | ✅ Completed |
| **Dashboarding & Visualization** | ✅ Completed |

---

## 🔮 Pengembangan Selanjutnya

Tahap berikutnya dari proyek ini meliputi:

- [x] Mendesain dashboard analytics
- [x] Menghubungkan Apache Superset ke ClickHouse
- [x] Membuat visualisasi KPI revenue dan order
- [x] Membuat visualisasi performa produk dan channel
- [x] Menggunakan `sales_forecast_ready` untuk analisis tren dan forecasting
- [x] Menambahkan visualisasi Geospatial

---

## 👤 Author

| | |
|---|---|
| **Project** | Smart Business Decision Data Warehouse |
| **Course** | Kecerdasan Bisnis dan Analitik |
| **Focus** | Data Warehouse Implementation |
| **Author** | Prayoga Adi Setyawan |
| **GitHub** | [@setyawannn](https://github.com/setyawannn) |
| **Repository** | [smart-business-decision-dw](https://github.com/setyawannn/smart-business-decision-dw) |
