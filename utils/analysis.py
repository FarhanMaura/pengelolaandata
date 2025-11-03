import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

class SalesAnalyzer:
    def __init__(self):
        pass
    
    def analyze_sales(self, df):
        """Analisis penjualan dengan statistik yang benar"""
        analysis = {}
        
        try:
            # Basic Statistics
            analysis['basic_stats'] = self._get_accurate_stats(df)
            
            # Category Analysis
            analysis['category_analysis'] = self._analyze_categories(df)
            
            # Top Products
            analysis['top_products'] = self._analyze_top_products(df)
            
            # Sales Trends
            analysis['sales_trends'] = self._analyze_sales_trends(df)
            
            # Visualizations
            analysis['visualizations'] = self._create_visualizations(df)
            
            analysis['success'] = True
            
        except Exception as e:
            analysis['success'] = False
            analysis['error'] = str(e)
        
        return analysis
    
    def _get_accurate_stats(self, df):
        """Statistik yang akurat dan meaningful"""
        total_sales = df['penjualan_rp'].sum()
        total_quantity = df['jumlah_terjual'].sum()
        
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
        
        # Validasi statistik
        self._validate_stats(stats)
        
        return stats
    
    def _validate_stats(self, stats):
        """Validasi statistik untuk memastikan keakuratan"""
        print(f"\n=== STATISTICS VALIDATION ===")
        print(f"Total Sales: Rp{stats['total_sales']:,.0f}")
        print(f"Total Products: {stats['total_products']}")
        print(f"Total Quantity: {stats['total_quantity']:,.0f}")
        print(f"Avg Price per Unit: Rp{stats['avg_price_per_unit']:,.0f}")
        print(f"Avg Sales per Product: Rp{stats['avg_sales_per_product']:,.0f}")
        
        # Validasi business logic
        if stats['avg_price_per_unit'] > 50000:
            print("⚠️  Warning: Average price seems high for restaurant")
        if stats['avg_sales_per_product'] > 10000000:
            print("⚠️  Warning: Average sales per product seems high")
    
    def _analyze_categories(self, df):
        """Analisis berdasarkan kategori"""
        if 'kategori' not in df.columns:
            return {}
        
        category_stats = df.groupby('kategori').agg({
            'penjualan_rp': ['sum', 'mean', 'count'],
            'jumlah_terjual': 'sum'
        }).round(2)
        
        category_stats.columns = ['total_sales', 'avg_sales', 'product_count', 'total_quantity']
        return category_stats.to_dict('index')
    
    def _analyze_top_products(self, df, top_n=10):
        """Analisis produk teratas"""
        if 'penjualan_rp' not in df.columns:
            return []
        
        top_products = df.nlargest(top_n, 'penjualan_rp')[
            ['produk', 'penjualan_rp', 'jumlah_terjual', 'kategori']
        ].to_dict('records')
        
        return top_products
    
    def _analyze_sales_trends(self, df):
        """Analisis tren penjualan"""
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
        """Buat visualisasi"""
        visualizations = {}
        
        try:
            # Top products chart
            visualizations['top_products'] = self._create_top_products_chart(df)
            
            # Category distribution
            visualizations['category_distribution'] = self._create_category_chart(df)
            
        except Exception as e:
            print(f"Visualization error: {e}")
        
        return visualizations
    
    def _create_top_products_chart(self, df):
        """Chart produk teratas"""
        plt.figure(figsize=(12, 8))
        
        top_10 = df.nlargest(10, 'penjualan_rp')
        products = top_10['produk'].apply(lambda x: x[:20] + '...' if len(x) > 20 else x)
        sales = top_10['penjualan_rp'] / 1000000  # Convert to millions
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        plt.barh(products, sales, color=colors[:len(products)])
        plt.title('10 Produk dengan Penjualan Tertinggi (Juta Rupiah)')
        plt.xlabel('Penjualan (Juta Rp)')
        plt.tight_layout()
        
        return self._plot_to_base64()
    
    def _create_category_chart(self, df):
        """Chart distribusi kategori"""
        plt.figure(figsize=(10, 8))
        
        category_sales = df.groupby('kategori')['penjualan_rp'].sum() / 1000000
        
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc',
                 '#c2c2f0', '#ffb3e6', '#c4e17f', '#76d7c4', '#f7c6c7']
        
        plt.pie(category_sales.values, labels=category_sales.index, autopct='%1.1f%%', 
                colors=colors[:len(category_sales)])
        plt.title('Distribusi Penjualan per Kategori')
        
        return self._plot_to_base64()
    
    def _plot_to_base64(self):
        """Convert plot to base64"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"