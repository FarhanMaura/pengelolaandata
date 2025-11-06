import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
import io
import base64
from typing import Dict, Any, List


class SalesAnalyzer:
    def __init__(self):
        pass
    
    def analyze_sales(self, df):
        """Analisis penjualan dengan statistik dan visualisasi"""
        analysis = {}
        
        try:
            analysis['basic_stats'] = self._get_accurate_stats(df)
            analysis['category_analysis'] = self._analyze_categories(df)
            analysis['top_products'] = self._analyze_top_products(df)
            analysis['sales_trends'] = self._analyze_sales_trends(df)
            analysis['favorite_menus'] = self.analyze_favorite_menus(df)  # TAMBAHAN BARU
            analysis['visualizations'] = self._create_visualizations(df)
            analysis['success'] = True
        except Exception as e:
            analysis['success'] = False
            analysis['error'] = str(e)
        
        return analysis

    def analyze_favorite_menus(self, df, top_n=10):
        """Analisis menu favorit berdasarkan frekuensi transaksi relatif"""
        try:
            # Buat salinan dataframe untuk analisis
            analysis_df = df.copy()
            
            # Jika ada kolom jumlah_terjual, gunakan langsung
            if 'jumlah_terjual' in analysis_df.columns and analysis_df['jumlah_terjual'].notna().any() and analysis_df['jumlah_terjual'].sum() > 0:
                # Gunakan jumlah_terjual langsung jika tersedia
                favorite_menus_df = analysis_df.nlargest(top_n, 'jumlah_terjual')[
                    ['produk', 'jumlah_terjual', 'penjualan_rp', 'kategori']
                ]
                
                favorite_analysis = []
                for _, menu in favorite_menus_df.iterrows():
                    favorite_analysis.append({
                        'produk': menu['produk'],
                        'jumlah_transaksi': int(menu['jumlah_terjual']),
                        'penjualan_rp': menu['penjualan_rp'],
                        'kategori': menu.get('kategori', 'Tidak Diketahui'),
                        'ranking_method': 'Jumlah Transaksi Langsung'
                    })
                
                return {
                    'success': True,
                    'favorite_menus': favorite_analysis,
                    'method': 'absolute_quantity',
                    'total_analyzed': len(favorite_analysis)
                }
            
            # Jika ada kolom persentase_terjual
            elif 'persentase_terjual' in analysis_df.columns and analysis_df['persentase_terjual'].notna().any():
                favorite_menus_df = analysis_df.nlargest(top_n, 'persentase_terjual')[
                    ['produk', 'persentase_terjual', 'penjualan_rp', 'kategori']
                ]
                
                favorite_analysis = []
                for _, menu in favorite_menus_df.iterrows():
                    favorite_analysis.append({
                        'produk': menu['produk'],
                        'persentase_transaksi': round(menu['persentase_terjual'], 2),
                        'penjualan_rp': menu['penjualan_rp'],
                        'kategori': menu.get('kategori', 'Tidak Diketahui'),
                        'ranking_method': 'Persentase Transaksi'
                    })
                
                return {
                    'success': True,
                    'favorite_menus': favorite_analysis,
                    'method': 'percentage_based',
                    'total_analyzed': len(favorite_analysis)
                }
            
            # Jika tidak ada data transaksi, estimasi dari penjualan
            elif 'penjualan_rp' in analysis_df.columns:
                # Estimasi frekuensi transaksi berdasarkan nilai penjualan
                # Asumsi: produk dengan penjualan tinggi kemungkinan lebih sering dipesan
                total_sales = analysis_df['penjualan_rp'].sum()
                
                # Normalisasi penjualan untuk estimasi frekuensi relatif
                analysis_df['estimated_frequency'] = (analysis_df['penjualan_rp'] / total_sales) * 100
                
                # Urutkan berdasarkan estimasi frekuensi
                favorite_menus_df = analysis_df.nlargest(top_n, 'estimated_frequency')[
                    ['produk', 'penjualan_rp', 'estimated_frequency', 'kategori']
                ]
                
                # Format hasil
                favorite_analysis = []
                for _, menu in favorite_menus_df.iterrows():
                    favorite_analysis.append({
                        'produk': menu['produk'],
                        'estimated_frequency': round(menu['estimated_frequency'], 2),
                        'penjualan_rp': menu['penjualan_rp'],
                        'kategori': menu.get('kategori', 'Tidak Diketahui'),
                        'ranking_method': 'Estimasi dari Nilai Penjualan'
                    })
                
                return {
                    'success': True,
                    'favorite_menus': favorite_analysis,
                    'method': 'estimated_from_sales',
                    'total_analyzed': len(favorite_analysis),
                    'note': 'Frekuensi transaksi diestimasi dari nilai penjualan relatif'
                }
            
            else:
                return {
                    'success': False,
                    'error': 'Data tidak cukup untuk analisis menu favorit. Kolom yang diperlukan: jumlah_terjual, persentase_terjual, atau penjualan_rp'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error dalam analisis menu favorit: {str(e)}'
            }
    

    def _get_accurate_stats(self, df):
        """Statistik utama"""
        total_sales = df['penjualan_rp'].sum()
        total_quantity = df['jumlah_terjual'].sum() if 'jumlah_terjual' in df.columns else 0
        
        stats = {
            'total_products': len(df),
            'total_sales': total_sales,
            'total_quantity': total_quantity,
            'avg_sales_per_product': df['penjualan_rp'].mean(),
            'avg_price_per_unit': total_sales / total_quantity if total_quantity > 0 else 0,
            'max_sales': df['penjualan_rp'].max(),
            'min_sales': df['penjualan_rp'].min(),
            'median_sales': df['penjualan_rp'].median()
        }
        return stats
    

    def _analyze_categories(self, df):
        if 'kategori' not in df.columns:
            return {}
        
        category_stats = df.groupby('kategori').agg({
            'penjualan_rp': ['sum', 'mean', 'count'],
            'jumlah_terjual': 'sum' if 'jumlah_terjual' in df.columns else 'count'
        }).round(2)
        category_stats.columns = ['total_sales', 'avg_sales', 'product_count', 'total_quantity']
        return category_stats.to_dict('index')
    

    def _analyze_top_products(self, df, top_n=10):
        if 'penjualan_rp' not in df.columns:
            return []
        
        top_products = df.nlargest(top_n, 'penjualan_rp')[
            ['produk', 'penjualan_rp', 'jumlah_terjual' if 'jumlah_terjual' in df.columns else 'produk', 'kategori']
        ].to_dict('records')
        return top_products
    

    def _analyze_sales_trends(self, df):
        trends = {}
        if 'penjualan_rp' in df.columns:
            sales_data = df['penjualan_rp']
            trends['sales_distribution'] = {
                'q1': sales_data.quantile(0.25),
                'median': sales_data.median(),
                'q3': sales_data.quantile(0.75),
                'std': sales_data.std()
            }
        return trends
    

    def _create_visualizations(self, df):
        visualizations = {}
        try:
            visualizations['top_products'] = self._create_top_products_chart(df)
            visualizations['category_distribution'] = self._create_category_pie_chart(df)
            visualizations['favorite_menus'] = self._create_favorite_menus_chart(df)  # TAMBAHAN BARU
        except Exception as e:
            print(f"Visualization error: {e}")
            visualizations['category_distribution'] = self._create_fallback_chart()
        return visualizations

    def _create_favorite_menus_chart(self, df):
        """Buat chart visualisasi menu favorit"""
        try:
            plt.figure(figsize=(12, 8))
            
            # Analisis menu favorit
            favorite_analysis = self.analyze_favorite_menus(df, top_n=10)
            
            if not favorite_analysis['success'] or not favorite_analysis['favorite_menus']:
                return self._create_fallback_chart("Data menu favorit tidak tersedia")
            
            favorite_menus = favorite_analysis['favorite_menus']
            
            # Siapkan data untuk chart
            products = []
            values = []
            value_label = ""
            
            for menu in favorite_menus:
                product_name = menu['produk']
                # Potong nama produk jika terlalu panjang
                if len(product_name) > 25:
                    product_name = product_name[:25] + '...'
                products.append(product_name)
                
                # Tentukan nilai berdasarkan metode analisis
                if 'jumlah_transaksi' in menu:
                    values.append(menu['jumlah_transaksi'])
                    value_label = 'Jumlah Transaksi'
                elif 'persentase_transaksi' in menu:
                    values.append(menu['persentase_transaksi'])
                    value_label = 'Persentase Transaksi (%)'
                elif 'estimated_frequency' in menu:
                    values.append(menu['estimated_frequency'])
                    value_label = 'Estimasi Frekuensi (%)'
                else:
                    values.append(0)
            
            # Warna untuk chart
            colors = ['#4C9AFF', '#36CFC9', '#9254DE', '#F759AB', '#FFA940',
                     '#40A9FF', '#73D13D', '#B37FEB', '#FF85C0', '#FFD666']
            
            # Buat horizontal bar chart
            bars = plt.barh(products, values, color=colors[:len(products)], edgecolor='white', linewidth=1.5)
            
            # Customize chart
            method = favorite_analysis.get('method', 'unknown')
            if method == 'estimated_from_sales':
                title = '10 Menu Favorit (Estimasi dari Nilai Penjualan)'
            elif method == 'percentage_based':
                title = '10 Menu Favorit (Berdasarkan Persentase Transaksi)'
            elif method == 'absolute_quantity':
                title = '10 Menu Favorit (Berdasarkan Jumlah Transaksi)'
            else:
                title = '10 Menu Favorit'
            
            plt.title(f'{title}\n', fontsize=14, fontweight='bold', color='#3c3c3c', pad=20)
            plt.xlabel(value_label, fontsize=12)
            
            plt.gca().invert_yaxis()
            plt.grid(axis='x', alpha=0.3)
            plt.gca().set_facecolor('#f9f9ff')
            
            # Tambah nilai di bar
            for bar in bars:
                width = bar.get_width()
                if 'persentase' in value_label.lower() or 'frekuensi' in value_label.lower():
                    label_text = f'{width:.1f}%'
                else:
                    label_text = f'{width:,.0f}'
                
                plt.text(width + (max(values) * 0.01), bar.get_y() + bar.get_height()/2,
                        label_text, va='center', fontsize=9, color='#595959')
            
            plt.tight_layout()
            return self._plot_to_base64()
            
        except Exception as e:
            print(f"Error creating favorite menus chart: {e}")
            return self._create_fallback_chart("Error membuat chart menu favorit")
    

    def _create_top_products_chart(self, df):
        """Bar chart 10 produk terlaris"""
        plt.figure(figsize=(12, 8))
        
        top_10 = df.nlargest(10, 'penjualan_rp')
        products = [str(p)[:25] + '...' if isinstance(p, str) and len(p) > 25 else str(p)
                    for p in top_10['produk']]
        sales = top_10['penjualan_rp'] / 1_000_000  # juta rupiah
        
        colors = ['#4C9AFF', '#36CFC9', '#9254DE', '#F759AB', '#FFA940',
                  '#40A9FF', '#73D13D', '#B37FEB', '#FF85C0', '#FFD666']
        
        bars = plt.barh(products, sales, color=colors[:len(products)], edgecolor='white', linewidth=1.5)
        plt.title('10 Produk dengan Penjualan Tertinggi (Juta Rupiah)',
                  fontsize=14, fontweight='bold', color='#3c3c3c', pad=20)
        plt.xlabel('Penjualan (Juta Rp)', fontsize=12)
        plt.gca().invert_yaxis()
        plt.grid(axis='x', alpha=0.3)
        plt.gca().set_facecolor('#f9f9ff')

        for bar in bars:
            width = bar.get_width()
            plt.text(width + 5, bar.get_y() + bar.get_height()/2,
                     f'{width:.1f}M', va='center', fontsize=9, color='#595959')

        plt.tight_layout()
        return self._plot_to_base64()
    

    def _create_category_pie_chart(self, df):
        """Pie chart distribusi kategori"""
        plt.figure(figsize=(8, 8))
        if 'kategori' not in df.columns or 'penjualan_rp' not in df.columns:
            return self._create_fallback_chart("Data kategori tidak tersedia")
        
        category_sales = df.groupby('kategori')['penjualan_rp'].sum().sort_values(ascending=False)
        top_categories = category_sales.head(6)
        
        colors = ['#4C9AFF', '#36CFC9', '#9254DE', '#F759AB', '#FFA940', '#73D13D']
        plt.pie(top_categories.values, labels=top_categories.index,
                autopct='%1.1f%%', startangle=90, colors=colors[:len(top_categories)],
                textprops={'fontsize': 10, 'color': '#333'}, wedgeprops={'edgecolor': 'white', 'linewidth': 2})

        plt.title('Distribusi Penjualan per Kategori',
                  fontsize=14, fontweight='bold', color='#3c3c3c', pad=20)
        plt.gca().set_facecolor('#f9f9ff')
        plt.tight_layout()
        return self._plot_to_base64()
    

    def _create_fallback_chart(self, message='Data tidak tersedia untuk visualisasi'):
        """Fallback chart jika data kosong"""
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, message,
                 ha='center', va='center', transform=plt.gca().transAxes,
                 fontsize=12, color='#666')
        plt.title('Visualisasi', color='#333')
        plt.gca().set_facecolor('#f9f9ff')
        return self._plot_to_base64()
    

    def _plot_to_base64(self):
        """Convert matplotlib plot jadi base64"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight',
                    facecolor='#ffffff', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return f"data:image/png;base64,{image_base64}"