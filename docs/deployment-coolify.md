# Coolify Deployment Guide

Dokumen ini menjelaskan cara deploy project `smart-business-decision-dw` ke Coolify sampai:

- dataset Kaggle diunduh otomatis dari Kaggle saat deploy
- file sumber di-rename otomatis ke `/data/raw/amazon_sale_report.csv`
- pipeline Bronze -> Silver -> Gold berjalan otomatis
- ClickHouse terisi
- Superset melakukan bootstrap dashboard otomatis
- dashboard siap dibuka untuk showcase

Dokumen ini mengikuti implementasi repo saat ini:

- `clickhouse` menyimpan warehouse
- `shared_data` menyimpan file mentah agar tetap ada antar redeploy
- `pipeline` mengunduh dataset Kaggle, menaruhnya ke lokasi final, lalu menjalankan seluruh ETL sekali jalan
- `superset` menunggu pipeline selesai lalu melakukan bootstrap dashboard
- `pipeline` diberi metadata `x-coolify.exclude_from_hc: true` agar intent Coolify terdokumentasi tanpa merusak validasi Docker Compose standar
- config dan bootstrap Superset dibake ke image Superset, bukan bergantung pada bind mount source repo
- ClickHouse berjalan sebagai service internal; hanya Superset yang perlu diarahkan ke domain publik
- pipeline tidak memakai `pandas/numpy`, jadi aman untuk CPU server lama yang tidak mendukung `X86_V2`

Referensi resmi Coolify yang dipakai:

- Docker Compose: [coolify.io/docs/knowledge-base/docker/compose](https://coolify.io/docs/knowledge-base/docker/compose)
- Environment Variables: [coolify.io/docs/knowledge-base/environment-variables](https://coolify.io/docs/knowledge-base/environment-variables)
- Terminal: [coolify.io/docs/knowledge-base/internal/terminal](https://coolify.io/docs/knowledge-base/internal/terminal)
- Persistent Storage: [coolify.io/docs/knowledge-base/persistent-storage](https://coolify.io/docs/knowledge-base/persistent-storage)

## Arsitektur Deploy

Stack Docker Compose di Coolify terdiri dari 3 service utama:

1. `clickhouse`
2. `pipeline`
3. `superset`

Urutan jalannya:

1. Coolify menjalankan `clickhouse`
2. Setelah `clickhouse` sehat, service `pipeline` mengunduh dataset Kaggle
3. `pipeline` mengekstrak file, mencari file CSV yang sesuai, lalu menyalinnya ke `/app/data/raw/amazon_sale_report.csv`
4. `pipeline` membuat ulang Bronze/Silver/Gold secara bersih dan mengisi data
5. Setelah `pipeline` sukses, `superset` start
6. `superset` bootstrap koneksi database, dataset virtual, chart, dan dashboard

## Prasyarat

- Server sudah terhubung ke Coolify
- Coolify dapat mengakses repo Git project ini
- Minimal 4 GB RAM, lebih nyaman 8 GB
- Domain atau subdomain untuk Superset bila ingin public showcase
- Akun Kaggle dan API credentials (`KAGGLE_USERNAME`, `KAGGLE_KEY`)

## Opsi Resource di Coolify

Gunakan salah satu dari dua model berikut:

1. `Application` berbasis Git Repository + Docker Compose
2. `Service` berbasis Docker Compose manual

Untuk project ini, yang paling nyaman adalah `Application` dari Git Repository karena setiap perubahan repo bisa langsung redeploy.

## Langkah 1: Tambah Resource di Coolify

1. Buka Coolify.
2. Pilih `New Resource`.
3. Pilih `Application`.
4. Hubungkan repository project ini.
5. Pilih build pack `Docker Compose`.
6. Pastikan file yang dipakai adalah `docker-compose.yml`.

Catatan:
Di deployment Docker Compose, file compose adalah sumber konfigurasi utama. Itu sesuai dengan dokumentasi resmi Coolify.

## Langkah 2: Isi Environment Variables di Coolify

Tambahkan environment variable berikut di UI Coolify.

```env
SUPERSET_SECRET_KEY=change_this_with_a_long_random_secret
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=change_this_admin_password
SUPERSET_ADMIN_EMAIL=admin@example.com
SUPERSET_ADMIN_FIRSTNAME=Smart
SUPERSET_ADMIN_LASTNAME=DW
SUPERSET_PORT=8088

CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_NATIVE_PORT=9000
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

Catatan penting:

- `CLICKHOUSE_SERVER_*` dipakai service ClickHouse internal dan pipeline admin; `CLICKHOUSE_SERVER_PASSWORD` wajib diisi agar ClickHouse tidak menonaktifkan akses network user `default`
- compose mengaktifkan `CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` agar pipeline bisa membuat atau memperbarui user Superset
- `CLICKHOUSE_USER` dan `CLICKHOUSE_PASSWORD` dipakai oleh Superset untuk koneksi read-only
- pipeline membuat atau memperbarui user Superset read-only dari `CLICKHOUSE_USER` dan `CLICKHOUSE_PASSWORD`
- `PIPELINE_INPUT_FILE` adalah nama akhir file yang akan dipakai pipeline di folder `raw`
- `PIPELINE_DEBUG_KEEPALIVE=true` hanya dipakai saat debugging agar container `pipeline` tidak langsung mati setelah gagal
- `PIPELINE_AUTO_DOWNLOAD=true` membuat pipeline otomatis mengunduh dataset dari Kaggle saat deploy
- `PIPELINE_FORCE_DOWNLOAD=true` memaksa file sumber diunduh ulang walaupun `/data/raw/amazon_sale_report.csv` sudah ada
- `KAGGLE_SOURCE_FILENAME` adalah nama file CSV yang diharapkan di dalam arsip Kaggle
- user ClickHouse Superset dibuat otomatis oleh pipeline, jadi tidak perlu mount konfigurasi user XML tambahan

## Langkah 3: Deploy Sekali Jalan

Setelah semua env Kaggle dan ClickHouse diisi, Anda tidak perlu mengunggah file manual.

### 3A. Deploy dari Coolify

Klik `Deploy` pada resource Coolify. Saat deploy:

1. `clickhouse` start
2. `pipeline` otomatis mengunduh dataset dari Kaggle
3. file CSV di-rename ke `/data/raw/amazon_sale_report.csv`
4. ETL Bronze -> Silver -> Gold berjalan
5. `superset` bootstrap dan start

Untuk domain publik, pilih service `superset` dan arahkan domain ke container port `8088`. Jangan expose service `clickhouse` kecuali benar-benar diperlukan untuk debugging, karena Superset dan pipeline sudah mengaksesnya melalui network internal Compose.

### 3B. Deploy dari terminal lokal

Kalau Anda ingin jalankan seluruh stack dari terminal dengan satu perintah:

```bash
docker compose up -d --build
```

Dengan asumsi env Kaggle dan ClickHouse sudah terisi, perintah ini cukup untuk:

1. build image
2. start ClickHouse
3. download dataset Kaggle
4. rename dan simpan dataset ke volume shared
5. load warehouse
6. start Superset

## Langkah 4: Validasi Log

Urutan yang diharapkan:

1. `clickhouse` menjadi healthy
2. `pipeline` berjalan sekali, lalu exit sukses
3. `superset` start setelah pipeline selesai sukses

Catatan:
Pada deploy pertama, sangat wajar jika `superset` belum jalan sebelum `pipeline` selesai. Itu memang urutan yang diinginkan.

### Pipeline

Periksa log service `pipeline`. Anda harus melihat alur seperti:

```text
[pipeline] dataset_path=/app/data/raw/amazon_sale_report.csv
[pipeline] auto_download=True
[pipeline] kaggle_credentials_present=True
[pipeline] Loading raw Kaggle dataset...
[pipeline] Starting Kaggle dataset download...
[pipeline] Copied dataset source Amazon Sale Report.csv to /app/data/raw/amazon_sale_report.csv
[pipeline] clickhouse_context=host=clickhouse, port=8123, database=smart_dw, user=default
[pipeline] Connecting to ClickHouse at clickhouse:8123/smart_dw
[pipeline] Ensuring ClickHouse user for Superset exists: superset
[pipeline] Refreshing target tables...
[pipeline] Creating warehouse objects...
[pipeline] Inserting bronze data...
[pipeline] Running Silver and Gold transformations...
[pipeline] Validation results:
[pipeline] Pipeline completed successfully.
```

Kalau `pipeline` gagal terlalu cepat dan log sulit dibaca, ubah env berikut di Coolify lalu redeploy:

```env
PIPELINE_DEBUG_KEEPALIVE=true
```

Mode ini akan menahan container `pipeline` tetap hidup setelah error, sehingga Anda bisa membuka log dan terminal service dengan lebih mudah. Setelah debugging selesai, kembalikan ke:

```env
PIPELINE_DEBUG_KEEPALIVE=false
```

### Superset

Periksa log service `superset`. Anda harus melihat:

```text
[superset-start] Starting Superset database migration
[superset-start] Creating Superset admin user if needed
[superset-start] Initializing Superset permissions and roles
[superset-start] Bootstrapping Smart DW database, datasets, charts, and dashboard
Bootstrapped Smart DW ClickHouse and Smart Business Decision Dashboard
[superset-start] Starting Superset web server on 0.0.0.0:8088
Running on http://0.0.0.0:8088
```

Jika log berhenti lama di `Starting Superset database migration`, masalahnya berada di metadata DB/volume Superset, bukan di pipeline ClickHouse. Untuk deploy pertama yang belum punya dashboard penting, reset volume `superset_home` lalu redeploy agar SQLite metadata dibuat ulang bersih.

## Langkah 5: Buka Dashboard

Expose service `superset` di Coolify menggunakan domain atau subdomain. Karena Superset listen di container port `8088`, isi domain service Superset dengan port tersebut, misalnya `https://bi.example.com:8088` di field domain Coolify.

Contoh:

- `bi.example.com`
- `dashboard.example.com`

Login memakai kredensial admin dari environment variables Coolify.

Dashboard utama yang akan muncul:

- `Smart Business Decision Dashboard`

## Apa yang Otomatis Dikerjakan Pipeline

Service `pipeline` akan melakukan semua ini tanpa langkah manual tambahan:

1. Mengunduh dataset dari `KAGGLE_DATASET`
2. Mengekstrak arsip Kaggle
3. Mencari file CSV yang cocok dengan `KAGGLE_SOURCE_FILENAME`
4. Menyalin hasilnya ke `/app/data/raw/amazon_sale_report.csv`
5. Menormalkan nama kolom
6. Membuat atau refresh Bronze
7. Memuat data mentah ke `smart_dw.bronze_orders_raw`
8. Menjalankan transformasi Silver
9. Membuat dimension table
10. Membuat `fact_sales`
11. Membuat analytical tables:
   - `customer_rfm`
   - `channel_performance_summary`
   - `product_profitability_summary`
   - `sales_forecast_ready`
   - `geographic_performance_summary`
12. Menjalankan validasi row count dan quality checks

## Validasi Setelah Deploy

Periksa log `pipeline` untuk hasil validasi. Yang ideal:

- `bronze_rows` terisi
- `silver_rows` terisi
- `fact_sales_rows` terisi
- `null_order_id_in_silver = 0`
- `invalid_quantity_in_silver = 0`
- `negative_revenue_in_silver = 0`

Kalau ingin cek manual dari terminal service `clickhouse`:

```bash
clickhouse-client --database smart_dw --multiquery < /sql/validation/data_quality_checks.sql
```

## Redeploy Saat Dataset Diganti

Jika Anda ingin memaksa download ulang dataset dari Kaggle:

1. ubah env `PIPELINE_FORCE_DOWNLOAD=true`
2. lakukan `Redeploy` resource di Coolify atau jalankan lagi `docker compose up -d --build`
3. cek log service `pipeline`
4. setelah sukses, kembalikan `PIPELINE_FORCE_DOWNLOAD=false`

Karena service `pipeline` melakukan refresh target table, hasil warehouse akan dibangun ulang dari file terbaru.

## Troubleshooting

### Pipeline gagal karena file tidak ditemukan

Gejala:

```text
Dataset tidak ditemukan: /app/data/raw/amazon_sale_report.csv
```

Solusi:

- pastikan `PIPELINE_AUTO_DOWNLOAD=true`
- pastikan `KAGGLE_USERNAME` dan `KAGGLE_KEY` terisi
- cek `KAGGLE_DATASET` dan `KAGGLE_SOURCE_FILENAME`
- cek log awal `pipeline` untuk `dataset_exists=False` atau `raw_directory_files=[]`

### Pipeline gagal tetapi Coolify hanya menampilkan `exit 1`

Solusi:

- buka log service `pipeline` langsung dari UI Coolify, bukan hanya log deploy
- bila log masih terlalu singkat, set `PIPELINE_DEBUG_KEEPALIVE=true` lalu redeploy
- cocokkan error ke salah satu kategori:
  - kredensial Kaggle belum diisi
  - download Kaggle gagal
  - file CSV di dalam arsip tidak cocok
  - kredensial user `pipeline` ClickHouse tidak cocok
  - koneksi ClickHouse gagal
  - parsing CSV gagal
  - SQL transform gagal

### Superset hidup tetapi chart kosong

Solusi:

- cek service `pipeline` sukses
- cek log `superset` memuat pesan bootstrap sukses
- buka ulang dashboard setelah hard refresh browser

### ClickHouse hidup tetapi Superset gagal konek

Solusi:

- pastikan `CLICKHOUSE_USER=superset`
- pastikan `CLICKHOUSE_PASSWORD` di Coolify sama dengan password user Superset yang dibuat pipeline
- redeploy resource setelah mengubah env

## Rekomendasi Showcase

Agar deployment kelihatan matang saat presentasi:

1. Siapkan subdomain khusus dashboard
2. Gunakan password admin yang rapi dan aman
3. Tunjukkan log `pipeline` sukses
4. Tunjukkan dashboard sudah otomatis muncul tanpa eksekusi SQL manual

## File Repo yang Mendukung Deploy Ini

- [docker-compose.yml](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/docker-compose.yml)
- [etl/run_pipeline.py](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/etl/run_pipeline.py)
- [etl/Dockerfile](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/etl/Dockerfile)
- [superset/bootstrap/bootstrap_superset.py](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/superset/bootstrap/bootstrap_superset.py)
