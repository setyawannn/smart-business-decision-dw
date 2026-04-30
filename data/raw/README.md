# Raw Dataset Folder

Folder ini digunakan untuk menyimpan file dataset mentah yang digunakan pada proses ETL.

## Dataset Source

Project ini menggunakan dataset: **E-Commerce Multi-Channel Sales Dataset**

Sumber dataset:
[Unlock Profits with E-Commerce Sales Data (Kaggle)](https://www.kaggle.com/datasets/thedevastator/unlock-profits-with-e-commerce-sales-data)

### Required Main File

File utama yang digunakan pada implementasi Data Warehouse adalah `amazon_sale_report.csv`.
Pastikan Anda mengunduh dan meletakkan file tersebut maupun dataset lainnya di dalam folder ini:
`data/raw/amazon_sale_report.csv`

### Important Notes

File CSV tidak diunggah ke GitHub repository karena ukurannya yang cukup besar.

Repository ini hanya menyimpan:
- Source code (Python ETL)
- SQL script (Bronze, Silver, Gold layer)
- Docker configuration (`docker-compose.yml`)
- Documentation & Diagrams
- Screenshots

**Perhatian:** Raw dataset harus diunduh secara manual dari Kaggle dan diletakkan pada folder ini sebelum Anda menjalankan pipeline ETL.