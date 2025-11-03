import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

class CustomerClustering:
    def __init__(self):
        self.scaler = StandardScaler()
    
    def perform_analysis(self, df):
        """Lakukan analisis clustering yang komprehensif"""
        try:
            # 1. Prepare features untuk clustering
            features_df = self._prepare_features(df)
            
            if features_df.empty or len(features_df) < 3:
                return {
                    'success': False,
                    'error': 'Tidak cukup data untuk clustering (minimal 3 data points)'
                }
            
            # 2. Tentukan jumlah cluster optimal
            optimal_clusters = self._find_optimal_clusters(features_df)
            
            # 3. Lakukan clustering
            clustering_results = self._perform_clustering(features_df, optimal_clusters)
            
            # 4. Analisis segmentasi pelanggan
            customer_segments = self._analyze_customer_segments(df, clustering_results['labels'])
            
            # 5. Siapkan visualisasi
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
        """Siapkan fitur-fitur untuk clustering"""
        features = {}
        
        # 1. Fitur berdasarkan penjualan
        if 'penjualan_rp' in df.columns:
            features['total_sales'] = df['penjualan_rp']
            if 'jumlah_terjual' in df.columns:
                # Hindari division by zero
                sales_per_unit = df['penjualan_rp'] / df['jumlah_terjual'].replace(0, 1)
                features['sales_per_unit'] = sales_per_unit
        
        # 2. Fitur berdasarkan kuantitas
        if 'jumlah_terjual' in df.columns:
            features['quantity_sold'] = df['jumlah_terjual']
        
        # 3. Fitur berdasarkan kategori (one-hot encoding)
        if 'kategori' in df.columns:
            category_dummies = pd.get_dummies(df['kategori'], prefix='cat')
            for col in category_dummies.columns:
                features[col] = category_dummies[col]
        
        # 4. Fitur profitabilitas
        if 'penjualan_rp' in df.columns and 'jumlah_terjual' in df.columns:
            # Normalize untuk menghindari nilai ekstrem
            normalized_sales = (df['penjualan_rp'] - df['penjualan_rp'].mean()) / df['penjualan_rp'].std()
            normalized_quantity = (df['jumlah_terjual'] - df['jumlah_terjual'].mean()) / df['jumlah_terjual'].std()
            features['profitability_score'] = normalized_sales * normalized_quantity
        
        features_df = pd.DataFrame(features)
        
        # Hapus kolom dengan variance 0
        features_df = features_df.loc[:, features_df.var() > 0]
        
        return features_df
    
    def _find_optimal_clusters(self, features_df, max_clusters=6):
        """Tentukan jumlah cluster optimal"""
        if len(features_df) <= 3:
            return 2
        
        scaled_features = self.scaler.fit_transform(features_df)
        
        max_clusters = min(max_clusters, len(features_df) - 1)
        
        wcss = []  # Within-cluster sum of squares
        silhouette_scores = []
        
        for k in range(2, max_clusters + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(scaled_features)
                wcss.append(kmeans.inertia_)
                if len(set(labels)) > 1:  # Pastikan ada lebih dari 1 cluster
                    silhouette_scores.append(silhouette_score(scaled_features, labels))
                else:
                    silhouette_scores.append(0)
            except:
                wcss.append(0)
                silhouette_scores.append(0)
        
        # Gunakan silhouette score sebagai primary metric
        if silhouette_scores:
            optimal_k = np.argmax(silhouette_scores) + 2
        else:
            optimal_k = 2
        
        return min(optimal_k, max_clusters)
    
    def _perform_clustering(self, features_df, n_clusters):
        """Lakukan clustering dengan K-Means"""
        scaled_features = self.scaler.fit_transform(features_df)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_features)
        
        # Hitung metrics
        if len(set(labels)) > 1:
            silhouette_avg = silhouette_score(scaled_features, labels)
        else:
            silhouette_avg = 0
        
        return {
            'labels': labels.tolist(),
            'centers': kmeans.cluster_centers_.tolist(),
            'inertia': kmeans.inertia_,
            'silhouette_score': silhouette_avg
        }
    
    def _analyze_customer_segments(self, df, labels):
        """Analisis karakteristik setiap segment"""
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = labels
        
        segments = {}
        
        for cluster_id in range(max(labels) + 1):
            cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]
            
            segment_info = {
                'segment_size': len(cluster_data),
                'total_sales': cluster_data['penjualan_rp'].sum() if 'penjualan_rp' in cluster_data.columns else 0,
                'avg_sales_per_product': cluster_data['penjualan_rp'].mean() if 'penjualan_rp' in cluster_data.columns else 0,
                'total_quantity': cluster_data['jumlah_terjual'].sum() if 'jumlah_terjual' in cluster_data.columns else 0,
            }
            
            # Add category stats if available
            if 'kategori' in cluster_data.columns:
                segment_info['top_categories'] = cluster_data['kategori'].value_counts().head(3).to_dict()
            
            # Add top products if available
            if 'produk' in cluster_data.columns and 'penjualan_rp' in cluster_data.columns:
                segment_info['top_products'] = cluster_data.nlargest(3, 'penjualan_rp')[['produk', 'penjualan_rp']].to_dict('records')
            
            # Beri nama segment berdasarkan karakteristik
            segment_info['segment_name'] = self._name_segment(segment_info)
            segment_info['recommendations'] = self._generate_recommendations(segment_info)
            
            segments[cluster_id] = segment_info
        
        return segments
    
    def _name_segment(self, segment_info):
        """Beri nama segment berdasarkan karakteristik"""
        avg_sales = segment_info['avg_sales_per_product']
        
        if avg_sales > 50000000:  # > 50 juta
            return "Produk Premium"
        elif avg_sales > 10000000:  # > 10 juta
            return "Produk High-Value"
        elif avg_sales > 1000000:   # > 1 juta
            return "Produk Medium-Value"
        else:
            return "Produk Standard"
    
    def _generate_recommendations(self, segment_info):
        """Generate rekomendasi bisnis untuk setiap segment"""
        recommendations = []
        
        segment_name = segment_info['segment_name']
        
        if segment_name == "Produk Premium":
            recommendations.extend([
                "Fokus pada kualitas dan experience pelanggan",
                "Tawarkan paket premium dengan nilai tambah",
                "Optimalkan inventory untuk produk high-margin"
            ])
        elif segment_name == "Produk High-Value":
            recommendations.extend([
                "Tingkatkan promosi dan visibility",
                "Bundle dengan produk complementary",
                "Monitor stock dan demand pattern"
            ])
        elif segment_name == "Produk Medium-Value":
            recommendations.extend([
                "Tingkatkan volume dengan promosi",
                "Optimalkan harga untuk competitive advantage",
                "Fokus pada customer retention"
            ])
        else:
            recommendations.extend([
                "Evaluasi profitability secara berkala",
                "Pertimbangkan bundle dengan produk high-value",
                "Monitor performance metrics"
            ])
        
        return recommendations
    
    def _prepare_visualizations(self, df, features_df, labels):
        """Siapkan visualisasi untuk clustering results"""
        visualizations = {}
        
        try:
            # 1. Cluster distribution pie chart
            visualizations['cluster_distribution'] = self._create_cluster_distribution_chart(labels)
            
            # 2. Sales by cluster bar chart
            visualizations['sales_by_cluster'] = self._create_sales_by_cluster_chart(df, labels)
            
        except Exception as e:
            print(f"Error creating visualizations: {e}")
        
        return visualizations
    
    def _create_cluster_distribution_chart(self, labels):
        """Buat pie chart distribusi cluster"""
        plt.figure(figsize=(8, 6))
        cluster_counts = pd.Series(labels).value_counts().sort_index()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        plt.pie(cluster_counts.values, 
                labels=[f'Segment {i}' for i in cluster_counts.index], 
                autopct='%1.1f%%', 
                startangle=90,
                colors=colors[:len(cluster_counts)])
        plt.title('Distribusi Segment Produk')
        
        return self._plot_to_base64()
    
    def _create_sales_by_cluster_chart(self, df, labels):
        """Buat bar chart penjualan per cluster"""
        plt.figure(figsize=(10, 6))
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = labels
        
        sales_by_cluster = df_with_clusters.groupby('cluster')['penjualan_rp'].sum() / 1000000  # Convert to millions
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        plt.bar([f'Segment {i}' for i in sales_by_cluster.index], 
                sales_by_cluster.values,
                color=colors[:len(sales_by_cluster)])
        plt.title('Total Penjualan per Segment (Juta Rupiah)')
        plt.xticks(rotation=45)
        plt.ylabel('Penjualan (Juta Rp)')
        plt.tight_layout()
        
        return self._plot_to_base64()
    
    def _plot_to_base64(self):
        """Convert plot to base64 string"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"