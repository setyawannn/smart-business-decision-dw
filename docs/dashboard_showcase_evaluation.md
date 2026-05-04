# 📊 Evaluasi dan Pemilihan Chart untuk Showcase Dashboard

Dokumen ini menjelaskan alasan di balik pemilihan setiap *chart* di "Smart Business Decision Dashboard" dan rekomendasi tambahan yang dapat diaplikasikan untuk keperluan *showcase* agar lebih menarik.

## 🎯 Mengapa Memilih Chart Ini?

Susunan *dashboard* yang kita buat mengikuti prinsip **"Overview to Detail"** (atau prinsip piramida piramida informasi), yang sangat direkomendasikan untuk presentasi bisnis.

1. **Big Number / KPI (Total Revenue, Orders, Qty, AOV)**
   - **Tujuan**: Menjawab pertanyaan *"Bagaimana kondisi bisnis kita secara keseluruhan?"* dalam 3 detik pertama.
   - **Alasan UI/UX**: Angka yang besar dan jelas di bagian paling atas *dashboard* membuat audiens langsung menangkap pencapaian utama perusahaan tanpa harus menebak-nebak.

2. **Daily Revenue & Orders Trend (Echarts Timeseries Line)**
   - **Tujuan**: Menunjukkan *pertumbuhan* dan *tren waktu*.
   - **Alasan UI/UX**: Garis waktu yang memiliki *smooth curve*, titik penanda, dan interaksi *tooltip* saat disentuh mempermudah analisis tren (seperti *seasonality*, lonjakan penjualan). Terdapat juga fitur "Forecast" bawaan Superset yang membuatnya terlihat canggih.

3. **Revenue by Category & Sub-Category (Echarts Bar - Vertical & Horizontal)**
   - **Tujuan**: Menganalisis performa berdasarkan portofolio produk.
   - **Alasan UI/UX**: Bar chart merupakan cara paling *human-readable* (mudah dibaca manusia) saat membandingkan entitas. Bar vertical untuk kategori utama, dan Bar horizontal untuk Sub-category menyajikan variasi tata letak agar audiens tidak bosan.

4. **Tabel Raw Data (Top Products & Channel Performance)**
   - **Tujuan**: *Deep-dive* dan pengecekan data spesifik.
   - **Alasan UI/UX**: Setiap analis dan manajer kadang butuh data angka pasti. Menambahkan fitur *Cell Bars* (bar ukuran di dalam tabel) membuat tabel tidak membosankan dan menyematkan rasa "visualisasi" bahkan pada angka tabular.

5. **Customer Segment Distribution (Pie/Donut Chart)**
   - **Tujuan**: Mengetahui profil kualitas *customer base* hasil pemodelan Machine Learning/Data Science (RFM Analysis).
   - **Alasan UI/UX**: *Donut Chart* jauh lebih modern dan estetik dibanding *Pie Chart* biasa. Ini menunjukkan bagaimana data yang rumit (Recency, Frequency, Monetary) direduksi menjadi profil bisnis (*Champions, Loyal*, dsb) yang cantik.

---

## 💡 Ide Tambahan untuk Memukau Audiens Saat Showcase

Jika ingin menambah **faktor "WoW"**, berikut adalah beberapa bagan/chart baru yang bisa Anda eksplorasi dan tambahkan ke dalam *dashboard*:

1. **Geographic Map Chart (Heatmap Peta) 🗺️**
   - **Data**: Karena Anda punya kolom `Country` (atau City dari dataset *raw*), membuat satu bagan tipe **Country Map** atau **Deck.gl Scatterplot** (jika ada *lon/lat*) dapat menarik perhatian ekstra karena Peta selalu memukau orang awam dan *C-Level*.
2. **Treemap / Sunburst Chart** 🍩
   - Sebagai pengganti Donut Chart atau untuk kategori produk, *Sunburst chart* sangat interaktif untuk melihat hierarki dari *Category* → *Sub Category* secara visual menumpuk.
3. **Gauge Chart untuk Target KPI**
   - Anda bisa menambahkan *Gauge chart* seperti *speedometer mobil* yang membandingkan pencapaian `Total Revenue` saat ini terhadap *Target Goal / Quota* bulanan. Manajer sangat menyukai tampilan target seperti ini.

---

## 🗣️ Panduan Presentasi: Mengambil Keputusan Bisnis (*Actionable Insights*)

Saat melakukan presentasi kepada audiens, eksekutif, atau pemangku kepentingan (dosen/manajer), tekankan dengan keras bahwa *dashboard* ini bukan sekadar gambar indikator pelaporan usang. Melainkan sebuah **"Mesin Pengambil Keputusan"**. 

Berikut adalah skenario contoh kalimat (naskah) bagi presentasi *showcase* Anda beserta keputusan operasionalnya:

**1. Analisis Peta (Geographic Map) 🗺️ ➔ Keputusan Ekspansi & Anggaran**
- *Kalimat Presentasi:* "Bapak/Ibu, dari peta interaktif (Geographic Revenue) ini, kita bisa melihat bahwa wilayah Maharashtra dan Karnataka menyumbang warna tergelap yang artinya menjadi lumbung transaksi dan *revenue* terbesar bagi e-commerce kita."
- *Rekomendasi Keputusan:* "Oleh karena itu, **keputusan yang kami buat** adalah merekomendasikan pembangunan *Fulfillment Center* (gudang pusat logistik) baru atau kerjasama ekspedisi kurir khusus di wilayah tersebut. Ini akan menurunkan ongkos kirim dan mempercepat durasi tibanya barang. Di lain sisi, wilayah terabaikan yang warnanya sangat terang/pudar dapat menjadi fokus *Ad-Spend* (anggaran iklan medsos) triwulan depan."

**2. Segmentasi Pelanggan (Donut Chart RFM) 🍩 ➔ Keputusan Program CRM & Penjualan**
- *Kalimat Presentasi:* "Kami tidak sekadar menghitung pelanggan. Kami mengkategorikan pelanggan secara sistematis (otomatis via sistem Data Warehouse) ke dalam model analisis _Recency, Frequency, Monetary_ (RFM)."
- *Rekomendasi Keputusan:* "Melihat porsi pelanggan di irisan **At Risk** & **Hibernating** cukup krusial, **keputusan untuk tim Marketing CRM** adalah segera melakukan ekstraksi basis data ID pelanggan golongan tersebut dan menghujaninya dengan *email/Blast Promo Win-Back* atau diskon besar-besaran agar aktif kembali. Sementara para **Champions** akan kita rekrut dalam fasilitas langganan VIP prioritas bebas ongkir agar loyalitas terjaga."

**3. Tren Performa Kategori (Bar Chart Series) 📊 ➔ Keputusan Inventory & Operasional Gudang**
- *Kalimat Presentasi:* "Secara hierarki penjualan di grafik Performa Kategori ini, produk dari kategori A (contoh pakaian/elektronik) terus-menerus unggul (bestseller), ketimbang kategori dasar lainnya yang seolah terabaikan di dasar (dead-stock)."
- *Rekomendasi Keputusan:* "**Keputusan untuk tim Supply Chain:** *restock* besar-besaran sebelum akhir bulan untuk Top 3 kategori saja agar tak kehabisan stok (*out-of-stock*). Untuk kategori terendah di bagian bawah grafik? Adakan program 'Cuci Gudang' / *Flash Sale Bundling* agar modal mati segera berputar lalu hapus dari etalase utama (delisting)."

**4. Grafik Tren Waktu / Daily Trends 📈 ➔ Keputusan Persiapan Tenaga Kerja Harian**
- *Kalimat Presentasi:* "Tren pergerakan harian yang terlihat mencolok membentuk bukit-lembah (*seasonality*). Ada pola spesifik seperti siklus lonjakan akhir minggu / jelang hari gajian."
- *Rekomendasi Keputusan:* "Data fluktuasi ini memandu **keputusan pendelegasian sumber daya:** Tim HR dan Operasional dapat menjadwalkan tambahan jam kerja lembur (*overtime*) pekerja pengepakan di hari rentan (misal h-1 *event* diskon), agar pengiriman tak *overload*, rasio ketepatan waktu terpenuhi, dan konsumen tak menulis *rating* buruk."