# Coolify Deployment Guide

Dokumen ini menjelaskan cara deploy project `smart-business-decision-dw` ke Coolify sampai:

- dataset Kaggle masuk ke folder `raw` pada persistent storage Coolify
- pipeline Bronze -> Silver -> Gold berjalan otomatis
- ClickHouse terisi
- Superset melakukan bootstrap dashboard otomatis
- dashboard siap dibuka untuk showcase

Dokumen ini mengikuti implementasi repo saat ini:

- `clickhouse` menyimpan warehouse
- `shared_data` menyimpan file mentah agar tetap ada antar redeploy
- `pipeline` menjalankan ETL dan seluruh SQL transformasi sekali jalan
- `superset` menunggu pipeline selesai lalu melakukan bootstrap dashboard

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
2. File Kaggle disimpan di persistent volume `shared_data`
3. Setelah `clickhouse` sehat, service `pipeline` membaca `/app/data/raw/amazon_sale_report.csv`
4. `pipeline` membuat ulang Bronze/Silver/Gold secara bersih dan mengisi data
5. Setelah `pipeline` sukses, `superset` start
6. `superset` bootstrap koneksi database, dataset virtual, chart, dan dashboard

## Prasyarat

- Server sudah terhubung ke Coolify
- Coolify dapat mengakses repo Git project ini
- Minimal 4 GB RAM, lebih nyaman 8 GB
- Domain atau subdomain untuk Superset bila ingin public showcase
- Akun Kaggle dan API token `kaggle.json`

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
CLICKHOUSE_SERVER_PASSWORD=
CLICKHOUSE_USER=superset
CLICKHOUSE_PASSWORD=change_this_superset_password

PIPELINE_INPUT_FILE=amazon_sale_report.csv
PIPELINE_DEBUG_KEEPALIVE=false
```

Catatan penting:

- `CLICKHOUSE_SERVER_*` dipakai service ClickHouse internal
- `CLICKHOUSE_USER` dan `CLICKHOUSE_PASSWORD` dipakai oleh Superset untuk koneksi read-only
- `PIPELINE_INPUT_FILE` menentukan nama file dataset utama di folder `raw` pada persistent storage
- `PIPELINE_DEBUG_KEEPALIVE=true` hanya dipakai saat debugging agar container `pipeline` tidak langsung mati setelah gagal

## Langkah 3: Siapkan Dataset Kaggle

Project ini mengharapkan file utama berikut:

```text
/data/raw/amazon_sale_report.csv
```

Karena file dataset tidak disimpan di Git, letakkan file itu lewat terminal Coolify ke persistent storage yang dibagikan ke service `clickhouse` dan `pipeline`.

### 3A. Buka terminal Coolify

Gunakan terminal bawaan Coolify sesuai dokumentasi resmi:
[coolify.io/docs/knowledge-base/internal/terminal](https://coolify.io/docs/knowledge-base/internal/terminal)

Gunakan terminal pada service `clickhouse`, karena service ini selalu hidup dan memount storage `/data`.

### 3B. Unduh dataset dari Kaggle

Di terminal service `clickhouse`, jalankan:

```bash
mkdir -p ~/.kaggle
cat > ~/.kaggle/kaggle.json <<'EOF'
{"username":"KAGGLE_USERNAME","key":"KAGGLE_API_KEY"}
EOF
chmod 600 ~/.kaggle/kaggle.json
python3 -m pip install --user kaggle
mkdir -p /data/raw
kaggle datasets download -d thedevastator/unlock-profits-with-e-commerce-sales-data -p /tmp/kaggle-dw
python3 -m zipfile -e /tmp/kaggle-dw/unlock-profits-with-e-commerce-sales-data.zip /tmp/kaggle-dw/extracted
find /tmp/kaggle-dw/extracted -iname "*amazon*sale*report*.csv"
cp "/tmp/kaggle-dw/extracted/Amazon Sale Report.csv" "/data/raw/amazon_sale_report.csv"
```

Kalau nama file hasil ekstraksi berbeda, yang penting hasil akhirnya menjadi:

```text
/data/raw/amazon_sale_report.csv
```

### 3C. Verifikasi file

```bash
ls -lah /data/raw
```

Pastikan file `amazon_sale_report.csv` ada dan ukurannya tidak nol.

Kalau ingin lebih yakin, cek file persisnya:

```bash
ls -lah /data/raw/amazon_sale_report.csv
```

## Langkah 4: Deploy Stack

Klik `Deploy` di Coolify.

Urutan yang diharapkan:

1. `clickhouse` menjadi healthy
2. `pipeline` berjalan sekali, lalu exit sukses
3. `superset` start setelah pipeline selesai sukses

Catatan:
Pada deploy pertama, sangat wajar jika `superset` belum jalan sebelum `pipeline` selesai. Itu memang urutan yang diinginkan.

## Langkah 5: Validasi Log

### Pipeline

Periksa log service `pipeline`. Anda harus melihat alur seperti:

```text
[pipeline] dataset_path=/app/data/raw/amazon_sale_report.csv
[pipeline] dataset_exists=True
[pipeline] raw_directory_files=['amazon_sale_report.csv']
[pipeline] clickhouse_context=host=clickhouse, port=8123, database=smart_dw, user=default
Connecting to ClickHouse...
Loading raw Kaggle dataset...
Refreshing target tables...
Creating warehouse objects...
Inserting bronze data...
Running Silver and Gold transformations...
Validation results:
Pipeline completed successfully.
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
Bootstrapped Smart DW ClickHouse and Smart Business Decision Dashboard
Running on http://0.0.0.0:8088
```

## Langkah 6: Buka Dashboard

Expose service `superset` di Coolify menggunakan domain atau subdomain.

Contoh:

- `bi.example.com`
- `dashboard.example.com`

Login memakai kredensial admin dari environment variables Coolify.

Dashboard utama yang akan muncul:

- `Smart Business Decision Dashboard`

## Apa yang Otomatis Dikerjakan Pipeline

Service `pipeline` akan melakukan semua ini tanpa langkah manual tambahan:

1. Membaca `/app/data/raw/amazon_sale_report.csv`
2. Menormalkan nama kolom
3. Membuat atau refresh Bronze
4. Memuat data mentah ke `smart_dw.bronze_orders_raw`
5. Menjalankan transformasi Silver
6. Membuat dimension table
7. Membuat `fact_sales`
8. Membuat analytical tables:
   - `customer_rfm`
   - `channel_performance_summary`
   - `product_profitability_summary`
   - `sales_forecast_ready`
   - `geographic_performance_summary`
9. Menjalankan validasi row count dan quality checks

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

Jika Anda mengganti file Kaggle dengan file baru:

1. upload atau replace file di `/data/raw/amazon_sale_report.csv`
2. verifikasi file dengan `ls -lah /data/raw/amazon_sale_report.csv`
3. lakukan `Redeploy` resource di Coolify
4. cek log service `pipeline`
5. setelah `pipeline` sukses, cek `superset`

Karena service `pipeline` melakukan refresh target table, hasil warehouse akan dibangun ulang dari file terbaru.

## Troubleshooting

### Pipeline gagal karena file tidak ditemukan

Gejala:

```text
Dataset tidak ditemukan: /app/data/raw/amazon_sale_report.csv
```

Solusi:

- cek kembali file sudah berada di `/data/raw/amazon_sale_report.csv`
- cek nama file sesuai `PIPELINE_INPUT_FILE`
- cek log awal `pipeline` untuk `dataset_exists=False` atau `raw_directory_files=[]`

### Pipeline gagal tetapi Coolify hanya menampilkan `exit 1`

Solusi:

- buka log service `pipeline` langsung dari UI Coolify, bukan hanya log deploy
- bila log masih terlalu singkat, set `PIPELINE_DEBUG_KEEPALIVE=true` lalu redeploy
- cocokkan error ke salah satu kategori:
  - file input tidak ada
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
- pastikan `CLICKHOUSE_PASSWORD` sama dengan yang dipakai di `clickhouse/users.d/superset-user.xml`
- redeploy resource setelah mengubah env

## Rekomendasi Showcase

Agar deployment kelihatan matang saat presentasi:

1. Siapkan subdomain khusus dashboard
2. Gunakan password admin yang rapi dan aman
3. Simpan langkah Kaggle download di terminal history atau catatan presentasi
4. Tunjukkan log `pipeline` sukses
5. Tunjukkan dashboard sudah otomatis muncul tanpa eksekusi SQL manual

## File Repo yang Mendukung Deploy Ini

- [docker-compose.yml](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/docker-compose.yml)
- [etl/run_pipeline.py](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/etl/run_pipeline.py)
- [etl/Dockerfile](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/etl/Dockerfile)
- [superset/bootstrap/bootstrap_superset.py](D:/Kuliah/Semester%204/KBA/projects/smart-business-decision-dw/superset/bootstrap/bootstrap_superset.py)
