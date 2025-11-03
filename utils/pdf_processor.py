import pdfplumber
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Optional


class PDFProcessor:
    def __init__(self):
        # Total penjualan yang kamu tahu benar (boleh kamu ubah sesuai laporan)
        self.expected_total = 2867497901  

    def pdf_to_csv(self, pdf_path: str, csv_path: str) -> pd.DataFrame:
        """Extract data produk dari PDF dengan format Rupiah Indonesia"""
        all_products: List[Dict] = []
        extracted_total = 0

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                print(f"\nProcessing page {page_num + 1}")
                text = page.extract_text()
                if not text:
                    continue

                page_products = self._process_page_text(text)
                page_total = sum(p["penjualan_rp"] for p in page_products)
                extracted_total += page_total

                print(f"Page {page_num + 1}: {len(page_products)} products, Total: Rp{page_total:,.0f}")
                all_products.extend(page_products)

        if all_products:
            df = pd.DataFrame(all_products)
            df = self._final_validation(df, extracted_total)
        else:
            df = pd.DataFrame(columns=["produk", "jumlah_terjual", "penjualan_rp", "kategori", "tanggal"])

        df.to_csv(csv_path, index=False)
        return df

    def _process_page_text(self, text: str) -> List[Dict]:
        """Proses teks per halaman dan ekstrak semua produk"""
        products: List[Dict] = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line or any(keyword in line for keyword in ["SKU", "Outlet", "Kategori", "Laporan", "Periode", "Zona", "Pencarian"]):
                continue

            product_data = self._extract_product_from_line(line, products)
            if product_data:
                products.append(product_data)

        return products

    def _extract_product_from_line(self, line: str, products: List[Dict]) -> Optional[Dict]:
        """Ekstrak 1 produk dari 1 baris"""
        try:
            if "Rp" not in line:
                return None

            parts = line.split()
            product_name_parts = []
            for i, part in enumerate(parts):
                if part.startswith("Rp"):
                    break
                product_name_parts.append(part)

            if not product_name_parts:
                return None

            product_name = " ".join(product_name_parts)

            # Skip duplikat nama produk
            if any(p["produk"] == product_name for p in products):
                return None

            # Ambil quantity (cari pola angka dengan titik/koma)
            quantity = self._safe_find_quantity(parts)

            # Ambil nilai penjualan
            sales_amount = self._extract_sales_amount(parts)

            if product_name and sales_amount > 0:
                category = self._determine_category_smart(product_name)
                print(f"✓ {product_name[:30]:30} | Qty: {quantity:6,.0f} | Sales: Rp{sales_amount:12,.0f}")

                return {
                    "produk": product_name,
                    "jumlah_terjual": quantity,
                    "penjualan_rp": sales_amount,
                    "kategori": category,
                    "tanggal": datetime.now().date(),
                }

        except Exception as e:
            print(f"✗ Error parsing line: {e}")
            print(f"  -> {line}")
        return None

    def _safe_find_quantity(self, parts: List[str]) -> float:
        """Cari quantity dengan regex yang aman"""
        for part in parts:
            if re.match(r"^\d{1,3}(?:,\d{3})*(?:\.\d{2})?$", part):
                return self._parse_float_safe(part)
        return 0.0

    def _extract_sales_amount(self, parts: List[str]) -> float:
        """Cari nilai penjualan dari bagian yang dimulai dengan Rp"""
        for i, part in enumerate(parts):
            if part.startswith("Rp"):
                num_str = part
                # Gabungkan jika angka terpotong spasi
                j = i + 1
                while j < len(parts) and re.match(r"^[\d.,]+$", parts[j]):
                    num_str += parts[j]
                    j += 1
                return self._parse_float_safe(num_str)
        return 0.0

    def _parse_float_safe(self, text: str) -> float:
        """Konversi teks rupiah ke float (format Indonesia aware)"""
        try:
            # Hilangkan simbol non-angka
            clean_text = re.sub(r"[^\d,\.]", "", text)

            # Format Indonesia: titik = ribuan, koma = desimal
            if re.match(r"^\d{1,3}(\.\d{3})*(,\d{2})?$", clean_text):
                clean_text = clean_text.replace(".", "").replace(",", ".")
            else:
                clean_text = clean_text.replace(",", "")

            value = float(clean_text)

            # Jika nilai kecil tapi seharusnya juta (contoh: 7.000 → 7 juta)
            if value < 10000:
                value *= 1000

            return value
        except Exception:
            return 0.0

    def _determine_category_smart(self, product_name: str) -> str:
        """Kategorisasi produk"""
        product_name_upper = product_name.upper()

        category_mapping = {
            "PAKET AYAM": "Paket Ayam",
            "PAKET IKAN LELE": "Paket Ikan Lele",
            "PAKET IKAN NILA": "Paket Ikan Nila",
            "PAKET BEBEK": "Paket Bebek",
            "PAKET CUMI": "Paket Seafood",
            "PAKET UDANG": "Paket Seafood",
            "AYAM BAKAR": "Ayam Bakar",
            "AYAM GORENG": "Ayam Goreng",
            "IKAN LELE": "Ikan Lele",
            "IKAN NILA": "Ikan Nila",
            "BEBEK": "Bebek",
            "NASI": "Nasi",
            "ES": "Minuman",
            "TEH": "Minuman",
            "JUS": "Minuman",
            "SUSU": "Minuman",
            "MIE": "Mie",
            "KWETIAU": "Mie",
            "CUMI": "Seafood",
            "UDANG": "Seafood",
        }

        for keyword, category in category_mapping.items():
            if keyword in product_name_upper:
                return category
        return "Lainnya"

    def _final_validation(self, df: pd.DataFrame, extracted_total: float) -> pd.DataFrame:
        """Cek hasil akhir dan tampilkan statistik"""
        print("\n=== FINAL VALIDATION ===")
        print(f"Extracted total: Rp{extracted_total:,.0f}")
        print(f"Expected total:  Rp{self.expected_total:,.0f}")

        total_sales = df["penjualan_rp"].sum()
        avg_sales = df["penjualan_rp"].mean()
        accuracy = (total_sales / self.expected_total) * 100 if self.expected_total > 0 else 0

        print(f"\nTotal Produk: {len(df)}")
        print(f"Total Penjualan: Rp{total_sales:,.0f}")
        print(f"Rata-rata Penjualan: Rp{avg_sales:,.0f}")
        print(f"Akurasi terhadap total PDF: {accuracy:.2f}%")

        # Bersihkan data outlier
        df = df[df["penjualan_rp"] < 1_000_000_000]
        return df
