import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use('Agg')  # non-GUI backend (biar jalan di server)
import matplotlib.pyplot as plt
import io
import base64


class CustomerClustering:
    def __init__(self):
        self.scaler = StandardScaler()
    
    def perform_analysis(self, df):
        """Lakukan analisis clustering komprehensif"""
        try:
            # 1. Siapkan fitur
            features_df = self._prepare_features(df)
            if features_df.empty or len(features_df) < 3:
                return {
                    'success': False,
                    'error': 'Tidak cukup data untuk clustering (minimal 3 data points)'
                }

            # 2. Tentukan jumlah cluster optimal
            optimal_clusters = self._find_optimal_clusters(features_df)

            # 3. Jalankan clustering
            clustering_results = self._perform_clustering(features_df, optimal_clusters)

            # 4. Analisis segmentasi
            customer_segments = self._analyze_customer_segments(df, clustering_results['labels'])

            # 5. Visualisasi
            visualizations = self._prepare_visualizations(df, features_df, clustering_results['labels'])

            return {
                'success': True,
                'optimal_clusters': optimal_clusters,
                'clustering_results': clustering_results,
                'customer_segments': customer_segments,
                'visualizations': visualizations,
                'features_used': features_df.columns.tolist()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _prepare_features(self, df):
        """Siapkan fitur numerik dan kategorikal"""
        features = {}

        # Fitur penjualan
        if 'penjualan_rp' in df.columns:
            features['total_sales'] = df['penjualan_rp']
            if 'jumlah_terjual' in df.columns:
                sales_per_unit = df['penjualan_rp'] / df['jumlah_terjual'].replace(0, 1)
                features['sales_per_unit'] = sales_per_unit

        # Fitur kuantitas
        if 'jumlah_terjual' in df.columns:
            features['quantity_sold'] = df['jumlah_terjual']

        # Fitur kategori (one-hot)
        if 'kategori' in df.columns:
            category_dummies = pd.get_dummies(df['kategori'], prefix='cat')
            for col in category_dummies.columns:
                features[col] = category_dummies[col]

        # Fitur profitabilitas
        if 'penjualan_rp' in df.columns and 'jumlah_terjual' in df.columns:
            norm_sales = (df['penjualan_rp'] - df['penjualan_rp'].mean()) / df['penjualan_rp'].std()
            norm_qty = (df['jumlah_terjual'] - df['jumlah_terjual'].mean()) / df['jumlah_terjual'].std()
            features['profitability_score'] = norm_sales * norm_qty

        features_df = pd.DataFrame(features)

        # Hapus fitur tanpa variasi
        features_df = features_df.loc[:, features_df.var() > 0]

        return features_df

    def _find_optimal_clusters(self, features_df, max_clusters=6):
        """Gunakan Silhouette Score untuk menentukan cluster optimal"""
        if len(features_df) <= 3:
            return 2

        scaled = self.scaler.fit_transform(features_df)
        max_clusters = min(max_clusters, len(features_df) - 1)

        scores = []
        for k in range(2, max_clusters + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(scaled)
                if len(set(labels)) > 1:
                    scores.append(silhouette_score(scaled, labels))
                else:
                    scores.append(0)
            except:
                scores.append(0)

        return np.argmax(scores) + 2 if scores else 2

    def _perform_clustering(self, features_df, n_clusters):
        """Jalankan K-Means Clustering"""
        scaled = self.scaler.fit_transform(features_df)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled)

        # Shift numbering ke 1-based
        labels = [l + 1 for l in labels]

        silhouette_avg = silhouette_score(scaled, labels) if len(set(labels)) > 1 else 0

        return {
            'labels': labels,
            'centers': kmeans.cluster_centers_.tolist(),
            'inertia': kmeans.inertia_,
            'silhouette_score': silhouette_avg
        }

    def _analyze_customer_segments(self, df, labels):
        """Analisis karakteristik tiap segment"""
        df_clustered = df.copy()
        df_clustered['cluster'] = labels

        segments = {}
        for cluster_id in sorted(df_clustered['cluster'].unique()):
            cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]

            segment_info = {
                'segment_size': len(cluster_data),
                'total_sales': cluster_data['penjualan_rp'].sum() if 'penjualan_rp' in cluster_data.columns else 0,
                'avg_sales_per_product': cluster_data['penjualan_rp'].mean() if 'penjualan_rp' in cluster_data.columns else 0,
                'total_quantity': cluster_data['jumlah_terjual'].sum() if 'jumlah_terjual' in cluster_data.columns else 0,
            }

            if 'kategori' in cluster_data.columns:
                segment_info['top_categories'] = cluster_data['kategori'].value_counts().head(3).to_dict()

            if 'produk' in cluster_data.columns and 'penjualan_rp' in cluster_data.columns:
                segment_info['top_products'] = cluster_data.nlargest(3, 'penjualan_rp')[['produk', 'penjualan_rp']].to_dict('records')

            segment_info['segment_name'] = self._name_segment(segment_info)
            segment_info['recommendations'] = self._generate_recommendations(segment_info)

            segments[cluster_id] = segment_info

        return segments

    def _name_segment(self, segment_info):
        avg_sales = segment_info['avg_sales_per_product']
        if avg_sales > 50_000_000:
            return "Produk Premium"
        elif avg_sales > 10_000_000:
            return "Produk High-Value"
        elif avg_sales > 1_000_000:
            return "Produk Medium-Value"
        return "Produk Standard"

    def _generate_recommendations(self, segment_info):
        """Buat rekomendasi strategi tiap segment"""
        seg = segment_info['segment_name']
        if seg == "Produk Premium":
            return [
                "Fokus pada kualitas dan experience pelanggan",
                "Tawarkan paket premium dengan nilai tambah",
                "Optimalkan inventory untuk produk high-margin"
            ]
        elif seg == "Produk High-Value":
            return [
                "Tingkatkan promosi dan visibility",
                "Bundle dengan produk complementary",
                "Monitor stock dan demand pattern"
            ]
        elif seg == "Produk Medium-Value":
            return [
                "Tingkatkan volume dengan promosi",
                "Optimalkan harga untuk competitive advantage",
                "Fokus pada customer retention"
            ]
        return [
            "Evaluasi profitability secara berkala",
            "Pertimbangkan bundle dengan produk high-value",
            "Monitor performance metrics"
        ]

    def _prepare_visualizations(self, df, features_df, labels):
        """Siapkan grafik untuk hasil clustering"""
        vis = {}
        try:
            vis['cluster_distribution'] = self._create_cluster_distribution_chart(labels)
            vis['sales_by_cluster'] = self._create_sales_by_cluster_chart(df, labels)
        except Exception as e:
            print(f"Visualization error: {e}")
        return vis

    def _create_cluster_distribution_chart(self, labels):
        """PIE CHART - Distribusi segment"""
        plt.figure(figsize=(10, 8))
        counts = pd.Series(labels).value_counts().sort_index()
        
        # Warna feminine untuk pie chart
        colors = ['#ff6b9d', '#ff8fab', '#ffa7c4', '#ffb3d1', '#ffc2dd', '#9d4edd']
        
        # Buat pie chart dengan styling yang lebih baik
        wedges, texts, autotexts = plt.pie(
            counts.values,
            labels=[f'Segment {i}' for i in counts.index],
            autopct='%1.1f%%', 
            startangle=90,
            colors=colors[:len(counts)],
            textprops={'fontsize': 10, 'fontweight': 'bold', 'color': 'white'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        
        # Style persentase
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        plt.title('Distribusi Segment Produk\n', 
                 fontsize=14, fontweight='bold', color='#d94a7e', pad=20)
        
        # Background color
        plt.gca().set_facecolor('#fff5f7')
        plt.tight_layout()
        
        return self._plot_to_base64()

    def _create_sales_by_cluster_chart(self, df, labels):
        """BAR CHART - Penjualan per segment"""
        plt.figure(figsize=(12, 8))
        dfc = df.copy()
        dfc['cluster'] = labels
        
        # Group by cluster dan hitung total penjualan
        sales_by_cluster = dfc.groupby('cluster')['penjualan_rp'].sum() / 1_000_000  # Convert ke juta
        
        # Warna feminine gradient untuk bar chart
        colors = ['#ff6b9d', '#ff8fab', '#ffa7c4', '#ffb3d1', '#ffc2dd', '#9d4edd']
        
        # Buat bar chart
        bars = plt.bar(
            [f'Segment {i}' for i in sales_by_cluster.index],
            sales_by_cluster.values, 
            color=colors[:len(sales_by_cluster)],
            edgecolor='white',
            linewidth=2,
            alpha=0.8
        )
        
        plt.title('Total Penjualan per Segment\n(Juta Rupiah)', 
                 fontsize=14, fontweight='bold', color='#d94a7e', pad=20)
        plt.ylabel('Penjualan (Juta Rp)', fontsize=12, color='#ff6b9d')
        
        # Rotasi label x-axis
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}M', 
                    ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color='#d94a7e')
        
        # Style improvements
        plt.grid(axis='y', alpha=0.3, color='#ff9ec0')
        plt.gca().set_facecolor('#fff5f7')
        plt.tight_layout()
        
        return self._plot_to_base64()

    def _plot_to_base64(self):
        """Convert plot to base64 dengan background feminine"""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', 
                   facecolor='#fff5f7', edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode()
        plt.close()
        return f"data:image/png;base64,{img_base64}"