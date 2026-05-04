# LAPORAN 3: DESAIN DAN IMPLEMENTASI VISUALISASI DATA

**Proyek:** Smart Business Decision Data Warehouse  
**Author:** Prayoga Adi Setyawan  

---

## 1. PENDAHULUAN
Laporan ini merupakan dokumen ketiga sekaligus tahap akhir dalam rangkaian pengembangan *Smart Business Decision Data Warehouse*. Setelah *Product Requirements Document (PRD)* selesai disusun dan *Medallion Architecture* untuk *Data Warehouse* berhasil diimplementasikan di atas **ClickHouse**, tahap ini difokuskan pada penerjemahan data analitik (Gold Layer) menjadi visualisasi interaktif.

Platform yang digunakan untuk visualisasi adalah **Apache Superset**. Visualisasi ini didesain tidak hanya untuk menyajikan data secara estetik, melainkan juga untuk menjawab *Business Objectives* secara langsung, memantau *Key Performance Indicators (KPI)*, serta mendukung pengambilan keputusan (Actionable Insights) yang berpusat pada pelanggan, produk, kanal penjualan, dan wilayah geografis.

---

## 2. DEFINISI KPI DAN KEDALAMAN ANALISA
*Dashboard* ini dirancang dengan pendekatan *Overview to Detail*, menyajikan metrik makro di bagian atas sebelum turun ke analisis mikro. KPI yang diukur secara eksklusif selaras dengan PRD:

1. **Total Revenue & Total Profit**: Mengukur volume uang yang berhasil ditarik dan efisiensi produk perusahaan.
2. **Total Orders & Total Qty**: Melacak *throughput* transaksi dan pergerakan persediaan. 
3. **Average Order Value (AOV)**: Mengetahui rata-rata pembelanjaan keranjang tiap pelanggan untuk memandu strategi penetapan harga (*bundling/upselling*).
4. **Distribusi Segmen Pelanggan (RFM)**: Menilai kesehatan basis konsumen secara kedalaman analisis kualitatif (*Recency, Frequency, Monetary*).
5. **Persebaran Geografis**: Memantau daerah potensial serta daerah tertinggal sebagai acuan alokasi anggaran logistik dan pemasaran.

---

## 3. RELEVANSI VISUAL DAN PEMILIHAN GRAFIK
Dalam menyusun tampilan visual, setiap bagan diplih secara spesifik berdasarkan tipe data yang direpresentasikan guna menghindari ambiguitas dan *cognitive overload*:

- **KPI Scorecards (Big Numbers)**  
  Menampilkan angka agregat (Total Revenue, Orders, Qty, AOV). Angka disajikan dalam format *Smart Number* (misal 75.4M) agar sekilas mudah dibaca oleh eksekutif (C-Level).
  
- **Echarts Timeseries Line (Daily Revenue & Orders Trend)**  
  Memilih bagan garis (*line chart*) untuk data *time-series* harian guna melihat tren, *seasonality*, serta lonjakan periode waktu tertentu dengan pola garis kurva halus (*smooth curve*).
  
- **Donut Chart (Customer Segment Distribution)**  
  Pie chart biasa tidak lagi memadai; *Donut chart* digunakan untuk menujukkan porsi segmen pelanggan (*Champions, Loyal, At Risk*, dll.) karena memberikan ruang baca estetis dan perbandingan proposisi *Part-to-Whole* yang lebih modern.
  
- **Country Map / Heatmap (Geographic Revenue India)**  
  Alih-alih menggunakan tabel untuk daftar provinsi, penggunaan *Choropleth ISO-3166-2 Map* negara India digunakan untuk merepresentasikan kepadatan transaksi berbasis wilayah. Warna yang lebih pekat mencerminkan *Revenue* lebih tajam.

- **Vertical & Horizontal Bar Charts (Performa Hierarki Kategori)**  
  *Bar chart* vertikal digunakan membandingkan variabel level makro (Kategori Utama), sedangan *horizontal bar* digunakan untuk entitas string yang panjang (Sub-Kategori) agar label teks mudah dibaca (tidak terpotong).

- **Tabel Data Terperinci (Product & Channel Performance)**  
  Menggunakan tabel dinamis dilengkapi *Cell Bars* (bar mini dalam sel tabel) agar angka tabular memiliki rasa visual yang mempermudah pemeringkatan.

> *[Placeholder: Masukkan Screenshot Dashboard Keseluruhan di Sini]*

---

## 4. INTERAKTIVITAS DAN USER EXPERIENCE (UX)
Faktor *Human-Computer Interaction* sangat diutamakan agar pengguna tidak kebingungan.
- **Hierarki Navigasi:** Membentuk pola visual piramida (atas ke bawah), dari metrik umum (Big Number) ➔ Analisis Peta dan Segmen ➔ Analisis Tren Waktu ➔ Tabel produk spesifik.
- **Cepat dan Responsif:** Dengan dukungan *engine* analitik ClickHouse yang menggunakan konsep *columnar*, proses agregasi *dashboard* beroperasi di bawah 1 detik (*sub-second performance*).
- **Tooltip Detail:** Seluruh grafik interaktif ketika kursor pengguna melayang *(hover)*, sehingga label rinci dan angka pasti akan segera dimunculkan melalui *tooltip*.

> *[Placeholder: Masukkan Screenshot Tooltip Interaktif pada Peta/Grafik di Sini]*

---

## 5. ESTETIKA DAN DESAIN VISUAL (UI)
Desain visual dibangun di atas pakem konsistensi tema guna menjamin tampilan profesional:
1. **Skema Warna (*Linear Color Scheme*):** Konsisten menggunakan *lyftColors* (atau palet gradiasi yang sudah ditentukan) melintasi grafik peta, *pie chart*, maupun *bar chart*. Kontras warna ditekankan pada elemen positif dan netral agar tidak melelahkan mata.
2. **Whitespace:** Menerapkan manajemen CSS tata letak (*layout*) berjarak yang proporsional antar-komponen visual, mencegah *dashboard* terasa *cluttered* (berantakan/penuh sesak).
3. **Typography:** Pemilihan hierarki skala teks (*Header Font 0.38, Subheader 0.12*) secara presisi agar informasi terfokus.

---

## 6. INTEGRITAS DATA DAN VALIDASI 
Kesempurnaan visual tidak akan berguna tanpa integritas data (akurasi) di bilik dapur:
- **Clean Data Handling:** Angka tidak memiliki error nilai agregat. Nilai *null* atau anomali (*ship-state* kosong dsb.) dari basis data berhasil diisolasi di layer *Silver* dan dibenahi saat memasuki *Gold Layer* tanpa merusak *join* SQL ke Peta Tableau.
- **Konsistensi:** Angka *Total Revenue* di visualisasi Big Number 100% klop dengan hasil *Query Aggregation SUM* dari tabel `geographic_performance_summary` atau `fact_sales` pada ClickHouse (*zero data discrepancy*). Kalkulasi segmentasi RFM juga sudah divalidasi sesuai rentang periode data yang tersedia aktual (*May - June 2022*).

---

## 7. KESIMPULAN DAN ACTIONABLE INSIGHTS
*Dashboard* yang dibangun bukan hanya instrumen pelaporan yang interaktif dan estetik, melainkan sebuah **"Mesin Pengambil Keputusan"**. Beberapa tindakan konkrit yang bisa dicetuskan dari alat ini, antara lain:
1. **Optimasi Logistik Geografis:** Keputusan pembangunan *Fulfillment Center* atau kolaborasi prioritas ekspedisi langsung terfokus ke titik provinsi terpekat di peta (Contoh: *Maharashtra, Karnataka*) guna memangkas durasi ongkos pengiriman.
2. **Peluncuran Target CRM Prioritas:** Melalui *Donut Chart RFM*, manajemen dapat mengekspor *database* pelanggan di spektrum "At Risk" guna meluncurkan *email campaign* promosi untuk mengaktivasi transaksi pelanggan kembali (*Win-Back Strategy*).
3. **Kontrol Inventaris (Supply Chain):** Produk yang menjuarai tabel performa langsung diberikan kuota pelipatgandaan *re-stock* mingguan, melindungi e-commerce dari kerugian akibat stok aus (*Out of Stock*).

---
*Demikian dokumen laporan tentang "Desain dan Implementasi Visualisasi Data" untuk Smart Business Decision Data Warehouse.*
