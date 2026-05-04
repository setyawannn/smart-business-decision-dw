#!/bin/bash
# Download and Extract Kaggle Dataset
# Membutuhkan kaggle-cli terinstal dan API token (~/.kaggle/kaggle.json) tersedia.

set -e

echo "================================================="
echo "   Downloading Dataset from Kaggle"
echo "================================================="

# Pastikan kaggle CLI tersedia
if ! command -v kaggle &> /dev/null; then
    echo "[!] Kaggle CLI tidak ditemukan. Sedang mencoba instalasi via pip..."
    pip install kaggle
fi

# Direktori tujuan
TARGET_DIR="data/raw"
mkdir -p "$TARGET_DIR"

# Download dataset
echo "[1/3] Mengunduh dataset kaggle thedevastator/unlock-profits-with-e-commerce-sales-data..."
kaggle datasets download -d thedevastator/unlock-profits-with-e-commerce-sales-data -p "$TARGET_DIR"

# Mengekstrak
echo "[2/3] Mengekstrak file zip..."
unzip -q -o "$TARGET_DIR/unlock-profits-with-e-commerce-sales-data.zip" -d "$TARGET_DIR"

# Merename file Utama
echo "[3/3] Merename file utama sesuai standar pipeline ETL..."

# Kaggle dataset extracts with spacing. We handle possible name outputs here:
if [ -f "$TARGET_DIR/Amazon Sale Report.csv" ]; then
    mv "$TARGET_DIR/Amazon Sale Report.csv" "$TARGET_DIR/amazon_sale_report.csv"
    echo "  -> File berhasil direname menjadi amazon_sale_report.csv"
elif [ -f "$TARGET_DIR/amazon_sale_report.csv" ]; then
    echo "  -> File amazon_sale_report.csv sudah ada dan siap."
fi

# Clean up zip
rm -f "$TARGET_DIR/unlock-profits-with-e-commerce-sales-data.zip"

echo "================================================="
echo "          Dataset Selesai Disiapkan!             "
echo "================================================="
