# Penjelasan Chart Dashboard Superset

Dokumen ini menjelaskan fungsi setiap chart pada dashboard `Smart Business Decision Dashboard`, sumber data yang dipakai, letak forecasting, dan perubahan dari dua revisi terakhir. Dokumen ini dibuat agar presentasi dashboard lebih mudah dijelaskan dan agar reviewer paham bahwa revisi chart sudah diarahkan ke data warehouse yang lebih stabil.

## Ringkasan Dashboard

Dashboard ini dibuat untuk membaca performa penjualan e-commerce dari beberapa sudut:

- KPI utama: revenue, orders, quantity, dan average order value.
- Tren waktu: revenue, orders, dan quantity harian.
- Forecasting: prediksi baseline untuk revenue dari tabel `sales_forecast_result`.
- Breakdown bisnis: kategori, sub-kategori, channel, produk, segmentasi customer, dan lokasi.
- Validasi performa KPI: apakah performa naik/turun dibanding periode sebelumnya dan apakah memenuhi minimum.

Dashboard sekarang menghindari forecasting runtime bawaan Superset agar tidak muncul error seperti `prophet undefined`. Forecast dihitung di pipeline dan disimpan di ClickHouse.

## Letak Forecasting

Forecasting berada pada chart:

### `SBD - Revenue Forecast`

Chart ini adalah visual forecasting utama. Sumber datanya adalah tabel:

```text
smart_dw.sales_forecast_result
```

Kolom penting:

| Kolom | Fungsi |
|---|---|
| `sales_date` | tanggal data historis atau tanggal prediksi |
| `metric_name` | nama metrik, saat ini `Revenue` dan `Orders` |
| `actual_value` | nilai aktual historis |
| `forecast_value` | nilai prediksi masa depan |
| `lower_bound` | batas bawah prediksi |
| `upper_bound` | batas atas prediksi |
| `model_name` | nama model yang menghasilkan data |

Model awal yang dipakai adalah:

```text
moving_average_7d
```

Artinya forecast memakai rata-rata 7 hari terakhir sebagai baseline prediksi 30 hari ke depan. Model ini sengaja dibuat sederhana, stabil, dan deterministic agar aman di production. Jika nanti butuh model lebih advanced, pipeline bisa diganti ke Prophet, ARIMA, atau model ML lain tanpa mengubah chart Superset, selama tetap menulis hasilnya ke `sales_forecast_result`.

Perbedaan penting:

- `SBD - Revenue Forecast` adalah chart forecast final.
- `SBD - Revenue Forecast Ready` adalah chart data historis yang siap dipakai sebagai dasar forecasting.

## Penjelasan Chart

### `SBD - Total Revenue`

Chart ini menampilkan total revenue dari tabel `kpi_daily_snapshot`. Card utama menampilkan angka besar agar pembaca langsung menangkap nilai revenue pada periode aktif. Grafik tren revenue ditampilkan pada chart terpisah `SBD - Mini Revenue Trend` tepat di bawah card KPI.

Cara membaca:

- Angka besar menunjukkan total revenue pada periode filter aktif.
- Tren visual dibaca dari `SBD - Mini Revenue Trend`.
- Comparison atau indikator periode sebelumnya dapat dipakai jika tersedia pada konfigurasi Superset.

Bahasa presentasi:

> "Kartu ini menunjukkan total pendapatan pada periode yang dipilih. Untuk melihat arah pergerakannya, kita baca mini trend revenue tepat di bawah kartu KPI."

### `SBD - Total Orders`

Chart ini menampilkan jumlah order dari tabel `kpi_daily_snapshot`. Tren visualnya ditampilkan pada `SBD - Mini Orders Trend`.

Cara membaca:

- Angka besar adalah total order.
- Tren order dibaca dari `SBD - Mini Orders Trend`.
- Jika revenue naik tetapi order turun, kemungkinan ada kenaikan nilai transaksi per order.

Bahasa presentasi:

> "Total Orders dipakai untuk membaca volume transaksi. Ini penting karena revenue tinggi belum tentu berarti jumlah pembelian meningkat."

### `SBD - Total Quantity Sold`

Chart ini menampilkan total quantity terjual. Ini memenuhi KPI PRD v2 no. 4 karena metric time-series sekarang mencakup Daily Revenue, Daily Orders, dan Daily Quantity. Tren visualnya ditampilkan pada `SBD - Mini Quantity Trend`.

Cara membaca:

- Angka besar adalah jumlah item terjual.
- Tren quantity dibaca dari `SBD - Mini Quantity Trend`.
- Cocok dibandingkan dengan revenue untuk melihat perubahan volume barang.

Bahasa presentasi:

> "Quantity Sold menunjukkan jumlah item yang benar-benar terjual. Metrik ini melengkapi revenue dan orders agar analisis tidak hanya berbasis nilai transaksi."

### `SBD - Average Order Value`

Chart ini menunjukkan rata-rata nilai order. Sumbernya dari `kpi_daily_snapshot`, dengan rumus `revenue / orders`. Tren visualnya ditampilkan pada `SBD - Mini AOV Trend`.

Cara membaca:

- AOV naik berarti rata-rata nilai belanja per order meningkat.
- AOV turun bisa berarti pelanggan membeli lebih sedikit per transaksi atau komposisi produk berubah.

Bahasa presentasi:

> "Average Order Value membantu melihat kualitas transaksi. Kalau order stabil tetapi AOV naik, berarti tiap transaksi rata-rata menghasilkan nilai yang lebih besar."

### `SBD - Mini Revenue Trend`

Chart ini adalah garis tren kecil untuk revenue, diletakkan tepat di bawah `SBD - Total Revenue`. Sumbernya `kpi_daily_snapshot`.

Bahasa presentasi:

> "Mini Revenue Trend memperlihatkan arah revenue dari waktu ke waktu, sehingga angka besar di atasnya punya konteks pergerakan."

### `SBD - Mini Orders Trend`

Chart ini adalah garis tren kecil untuk orders, diletakkan tepat di bawah `SBD - Total Orders`. Sumbernya `kpi_daily_snapshot`.

Bahasa presentasi:

> "Mini Orders Trend membantu melihat apakah volume transaksi sedang meningkat, stabil, atau menurun."

### `SBD - Mini Quantity Trend`

Chart ini adalah garis tren kecil untuk quantity sold, diletakkan tepat di bawah `SBD - Total Quantity Sold`. Sumbernya `kpi_daily_snapshot`.

Bahasa presentasi:

> "Mini Quantity Trend menunjukkan perubahan jumlah item yang terjual dari waktu ke waktu."

### `SBD - Mini AOV Trend`

Chart ini adalah garis tren kecil untuk average order value, diletakkan tepat di bawah `SBD - Average Order Value`. Sumbernya `kpi_daily_snapshot`.

Bahasa presentasi:

> "Mini AOV Trend menunjukkan perubahan nilai rata-rata transaksi, sehingga kita bisa melihat apakah nilai belanja per order membaik atau melemah."

### `SBD - Geographic Revenue (India)`

Chart ini adalah map revenue per wilayah India. Sumber datanya sekarang `geographic_daily_summary`, bukan join lewat `dim_customer`.

Alasan perubahan:

- Sebelumnya map bisa tampak hitam di satu daerah karena `customer_id` pada `fact_sales` banyak bernilai `Unknown`.
- Sekarang map memakai `silver_orders_clean` sebagai sumber geografi sehingga `state` tetap lengkap.
- Validasi terakhir menunjukkan ada `67` state distinct.

Cara membaca:

- Warna lebih kuat berarti revenue lebih besar.
- Map ini dibuat paling lebar agar pembaca langsung melihat distribusi revenue geografis.

Bahasa presentasi:

> "Map ini menunjukkan persebaran revenue per state. Sumber geografi sudah dipindahkan langsung dari cleaned orders agar lokasi tidak hilang karena customer id yang tidak lengkap."

### `SBD - Channel Revenue and Orders`

Chart ini menampilkan performa channel berdasarkan revenue dan orders. Saat ini posisinya ditukar agar berada di area kanan map.

Cara membaca:

- `total_revenue` menunjukkan kontribusi nilai penjualan.
- `total_orders` menunjukkan volume transaksi per channel.
- Channel dengan revenue tinggi tetapi order lebih rendah bisa berarti nilai order rata-ratanya lebih besar.

Bahasa presentasi:

> "Chart channel membantu melihat jalur penjualan mana yang paling berkontribusi, baik dari sisi revenue maupun jumlah order."

### `SBD - Revenue Forecast`

Chart ini menampilkan garis aktual dan garis prediksi revenue. Sumbernya `sales_forecast_result`.

Cara membaca:

- `Actual Revenue` adalah data historis.
- `Forecast Revenue` adalah prediksi 30 hari ke depan.
- Model saat ini adalah baseline moving average 7 hari.
- Forecast ini tidak menggunakan fitur forecast Superset, sehingga aman dari error dependency Prophet.

Bahasa presentasi:

> "Forecasting di dashboard ini tidak dihitung oleh Superset saat runtime. Pipeline menghitung baseline forecast terlebih dahulu, menyimpannya ke ClickHouse, lalu Superset hanya menampilkan hasilnya. Ini membuat dashboard lebih stabil untuk production."

### `SBD - Revenue Forecast Ready`

Chart ini menampilkan data historis yang siap dipakai untuk forecasting. Sumbernya `sales_forecast_ready`.

Metric yang dipakai:

- `total_revenue`
- `total_orders`

Catatan:

- `total_profit` tidak dipakai di chart utama karena sumber data saat ini menghasilkan profit nol.
- Kolom profit tetap dipertahankan di warehouse untuk kompatibilitas schema.

Bahasa presentasi:

> "Chart ini menunjukkan data historis yang menjadi fondasi forecasting. Kita tidak memakai profit sebagai seri utama karena data sumber belum menyediakan profit yang valid."

### `SBD - Daily Revenue Trend`

Chart ini menampilkan tren revenue harian dari `sales_forecast_ready`.

Cara membaca:

- Dipakai untuk melihat fluktuasi pendapatan dari hari ke hari.
- Cocok untuk membaca pola spike atau penurunan harian.

Bahasa presentasi:

> "Daily Revenue Trend memperlihatkan perubahan pendapatan harian, sehingga pola naik turun lebih terlihat daripada hanya membaca total bulanan."

### `SBD - Daily Orders Trend`

Chart ini menampilkan tren jumlah order harian dari `sales_forecast_ready`.

Cara membaca:

- Jika order naik tetapi revenue tidak naik, kemungkinan nilai per order turun.
- Jika order turun tetapi revenue tetap tinggi, kemungkinan AOV naik.

Bahasa presentasi:

> "Daily Orders Trend menunjukkan perubahan volume transaksi. Ini membantu membedakan apakah performa didorong oleh jumlah pembelian atau nilai pembelian."

### `SBD - Daily Quantity Trend`

Chart ini menampilkan quantity terjual per hari dari `sales_forecast_ready`.

Cara membaca:

- Menunjukkan volume item yang keluar setiap hari.
- Melengkapi PRD v2 no. 4: Daily Revenue, Daily Orders, dan Daily Quantity.

Bahasa presentasi:

> "Daily Quantity Trend menutup kebutuhan forecast-ready metrics pada PRD v2 karena quantity sudah tersedia sebagai metrik harian."

### `SBD - Revenue by Category`

Chart ini menampilkan revenue berdasarkan kategori produk.

Cara membaca:

- Kategori dengan bar terbesar adalah kategori dengan kontribusi revenue terbesar.
- Dapat dipakai untuk menentukan kategori prioritas.

Bahasa presentasi:

> "Chart kategori menunjukkan area produk yang paling banyak menyumbang revenue."

### `SBD - Revenue by Sub-Category`

Chart ini menampilkan breakdown revenue yang lebih detail dari kategori.

Cara membaca:

- Membantu menemukan sub-kategori yang dominan.
- Berguna saat kategori terlalu umum dan perlu detail lebih tajam.

Bahasa presentasi:

> "Sub-category memberi detail tambahan supaya kita tidak hanya tahu kategori besar, tetapi juga bagian produk yang benar-benar kuat."

### `SBD - Monthly Revenue by Channel`

Chart ini menampilkan revenue bulanan per channel dari `channel_monthly_summary`.

Cara membaca:

- Membandingkan performa channel antar bulan.
- Karena memakai helper table bulanan, chart lebih stabil saat filter atau legend dipakai.

Bahasa presentasi:

> "Monthly Revenue by Channel menunjukkan perubahan kontribusi channel dari bulan ke bulan."

### `SBD - Top Products by Revenue`

Chart ini menampilkan produk dengan revenue tertinggi.

Cara membaca:

- Produk paling atas adalah produk dengan kontribusi revenue terbesar.
- `total_quantity` dan `total_orders` membantu membedakan produk bernilai tinggi dari produk dengan volume tinggi.

Bahasa presentasi:

> "Tabel ini memperlihatkan produk yang paling berkontribusi terhadap revenue, sekaligus volume dan jumlah order-nya."

### `SBD - Top States by Revenue`

Chart ini menampilkan ranking state berdasarkan revenue.

Cara membaca:

- Melengkapi map dengan bentuk tabel.
- Berguna ketika pembaca ingin melihat nama state dan angkanya secara eksplisit.

Bahasa presentasi:

> "Top States by Revenue adalah versi tabel dari map, sehingga wilayah dengan kontribusi tertinggi bisa dibaca lebih presisi."

### `SBD - Customer Segment Distribution`

Chart ini menampilkan distribusi segmentasi customer dari `customer_rfm`.

Cara membaca:

- Segmentasi membantu membaca komposisi customer berdasarkan perilaku pembelian.
- Dapat menjadi dasar strategi retensi atau targeting.

Bahasa presentasi:

> "Segmentasi customer membantu melihat komposisi pelanggan, bukan hanya transaksi. Ini bisa dipakai untuk membaca peluang retensi dan targeting."

### `SBD - KPI Performance Status`

Chart ini menampilkan status KPI dibanding periode sebelumnya.

Kolom penting:

| Kolom | Fungsi |
|---|---|
| `kpi_name` | nama KPI |
| `current_value` | nilai periode berjalan |
| `previous_value` | nilai periode pembanding |
| `delta_value` | selisih absolut |
| `delta_pct` | selisih persentase |
| `trend_direction` | naik/turun |
| `minimum_status` | memenuhi minimum atau belum |

Cara membaca:

- `Up` berarti nilai KPI naik dibanding periode sebelumnya.
- `Down` berarti nilai KPI turun.
- `Meets Minimum` berarti KPI memenuhi standar minimum.
- `Below Minimum` berarti KPI belum memenuhi standar minimum.

Bahasa presentasi:

> "KPI Performance Status dibuat agar pembaca tidak hanya melihat angka, tetapi langsung tahu apakah performanya naik atau turun dan apakah sudah memenuhi minimum."

## Revisi yang Sudah Dibenarkan dan Dirubah

### Revisi 1: Forecast error dan KPI PRD v2 no. 4

Masalah awal:

- Chart forecast Superset memunculkan error dependency seperti `prophet undefined`.
- `sales_forecast_ready` belum lengkap untuk PRD v2 no. 4 karena belum eksplisit memuat Daily Quantity.
- Beberapa chart time-series terlihat terlalu mirip.

Yang dibenarkan:

- Forecast runtime Superset dimatikan sebagai sumber prediksi.
- Forecast dipindahkan ke pipeline dan disimpan di `sales_forecast_result`.
- `sales_forecast_ready` sekarang memuat:
  - `sales_date`
  - `total_revenue`
  - `total_orders`
  - `total_quantity`
  - `total_profit`
- Ditambahkan chart `Daily Quantity Trend`.
- `Revenue Forecast`, `Revenue Forecast Ready`, `Daily Revenue Trend`, dan `Daily Orders Trend` dibuat berbeda fungsi:
  - `Revenue Forecast`: prediksi masa depan.
  - `Revenue Forecast Ready`: data historis agregat untuk readiness.
  - `Daily Revenue Trend`: tren revenue harian.
  - `Daily Orders Trend`: tren order harian.

### Revisi 2: Layout, KPI card, mini trend, map, dan interaksi chart

Masalah awal:

- KPI card hanya angka besar tanpa tren visual yang terlihat pada dashboard.
- Map sempat menjadi hitam/satu area karena sumber geo tidak stabil.
- Ada ruang kosong layout dan beberapa posisi chart belum sesuai.
- Chart `SBD - Revenue Forecast` sempat error `Metric 'actual_value' does not exist`.

Yang dibenarkan:

- KPI card tetap dipakai untuk angka utama.
- Tren visual KPI ditambahkan sebagai row mini trend terpisah tepat di bawah KPI cards.
- Mini trend memakai dataset `kpi_daily_snapshot` agar stabil.
- Map memakai `geographic_daily_summary`, yang dibangun langsung dari `silver_orders_clean`.
- `Channel Revenue and Orders` dipindahkan ke row kanan map.
- `KPI Performance Status` dipindahkan menjadi row full-width.
- `Revenue Forecast` dipindahkan sebelum `Revenue Forecast Ready`.
- Metric forecast diubah menjadi SQL metric:
  - `SUM(actual_value)` sebagai `Actual Revenue`
  - `SUM(forecast_value)` sebagai `Forecast Revenue`
- Helper table baru ditambahkan agar chart interaktif tidak mudah blank:
  - `kpi_daily_snapshot`
  - `geographic_daily_summary`
  - `channel_monthly_summary`

## Saran Alur Presentasi

Gunakan alur ini saat menjelaskan dashboard:

1. Mulai dari KPI utama.

   > "Pertama, kita lihat ringkasan performa: total revenue, total orders, quantity sold, dan average order value. Card di baris atas menunjukkan angka utama, lalu baris mini trend di bawahnya menunjukkan arah pergerakan tiap KPI."

2. Jelaskan status KPI.

   > "Setelah angka utama, tabel KPI Performance Status menunjukkan apakah setiap KPI naik atau turun dibanding periode sebelumnya dan apakah sudah memenuhi batas minimum."

3. Jelaskan peta dan channel.

   > "Bagian geografis menunjukkan persebaran revenue per state di India. Di sampingnya, channel revenue and orders memperlihatkan kontribusi jalur penjualan."

4. Jelaskan forecasting.

   > "Forecasting ada di chart Revenue Forecast. Prediksi tidak dihitung oleh Superset, tetapi dihitung di pipeline dan disimpan di ClickHouse. Dengan pendekatan ini dashboard lebih stabil karena tidak bergantung pada Prophet runtime di Superset."

5. Jelaskan forecast-ready metrics.

   > "Untuk memenuhi PRD v2 no. 4, tabel sales_forecast_ready menyimpan Daily Revenue, Daily Orders, dan Daily Quantity. Tiga metrik ini bisa dipakai untuk visualisasi tren maupun dasar forecasting tahap berikutnya."

6. Tutup dengan breakdown bisnis.

   > "Bagian bawah dashboard memperlihatkan breakdown kategori, sub-kategori, channel bulanan, top products, top states, dan segmentasi customer. Ini membantu berpindah dari ringkasan performa ke area bisnis yang perlu dianalisis lebih dalam."

## Catatan Teknis untuk Reviewer

- Forecast utama ada di `smart_dw.sales_forecast_result`.
- Forecast-ready history ada di `smart_dw.sales_forecast_ready`.
- KPI card memakai `smart_dw.kpi_daily_snapshot`.
- Map memakai `smart_dw.geographic_daily_summary`.
- Channel bulanan memakai `smart_dw.channel_monthly_summary`.
- Profit tidak dipakai di chart utama karena nilai profit dari sumber data masih nol.
- Rebuild local aman karena pipeline menghapus dan membangun ulang tabel turunan.
