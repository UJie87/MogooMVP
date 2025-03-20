import psycopg2
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import os
from datetime import datetime

# 確保輸出資料夾存在
output_folder = "power_usage_plots"
os.makedirs(output_folder, exist_ok=True)
print(f"輸出資料夾路徑：{os.path.abspath(output_folder)}")

try:
    # 連接資料庫
    print("開始連接資料庫...")
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="mogoodatabase",
        user="postgres",
        password="1234"
    )
    cursor = connection.cursor()
    
    # 獲取所有摘要表的數據
    print("\n收集數據進行分群分析...")
    all_results = []
    
    # 獲取摘要表列表（排除parking）
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'summary_%'
        AND table_name != 'summary_phison_parking'
    """)
    summary_tables = [table[0] for table in cursor.fetchall()]
    
    if not summary_tables:
        raise Exception("未找到任何符合條件的摘要表！")
    
    print(f"找到的摘要表：{', '.join(summary_tables)}")
    
    # 處理每個摘要表
    for table in summary_tables:
        site_name = table.replace('summary_', '')
        print(f"\n處理 {site_name} 的數據...")
        
        query = f"""
        WITH monthly_total AS (
            SELECT 
                year, 
                month, 
                SUM(total_usage) as total_monthly,
                CASE 
                    WHEN month IN (5,6,7,8,9,10) THEN 'summer'
                    ELSE 'nonsummer'
                END as season
            FROM {table}
            GROUP BY year, month
        ),
        seasonal_total AS (
            SELECT 
                year,
                SUM(CASE WHEN season = 'summer' THEN total_monthly ELSE 0 END) as summer_total,
                SUM(CASE WHEN season = 'nonsummer' THEN total_monthly ELSE 0 END) as nonsummer_total
            FROM monthly_total
            GROUP BY year
        ),
        usage_by_period AS (
            SELECT 
                year,
                month,
                SUM(CASE WHEN time_period = 'peak' THEN total_usage ELSE 0 END) as peak,
                SUM(CASE WHEN time_period = 'mid-peak' THEN total_usage ELSE 0 END) as midpeak,
                SUM(CASE WHEN time_period = 'off-peak' THEN total_usage ELSE 0 END) as offpeak,
                SUM(CASE WHEN time_period = 'Sat. mid-peak' THEN total_usage ELSE 0 END) as sat_midpeak
            FROM {table}
            GROUP BY year, month
        )
        SELECT 
            u.year,
            u.month,
            '{site_name}' as site,
            ROUND(COALESCE(u.peak / NULLIF(t.total_monthly, 0) * 100, 0), 2) as peak_ratio,
            CASE 
                WHEN u.month IN (1,2,3,4,11,12) 
                THEN ROUND(COALESCE(u.midpeak / NULLIF(t.total_monthly, 0) * 100, 0), 2)
                ELSE NULL 
            END as nonsummer_midpeak_ratio,
            CASE 
                WHEN u.month IN (5,6,7,8,9,10) 
                THEN ROUND(COALESCE(u.midpeak / NULLIF(t.total_monthly, 0) * 100, 0), 2)
                ELSE NULL 
            END as summer_midpeak_ratio,
            CASE 
                WHEN u.month IN (1,2,3,4,11,12) 
                THEN ROUND(COALESCE(u.offpeak / NULLIF(t.total_monthly, 0) * 100, 0), 2)
                ELSE NULL 
            END as nonsummer_offpeak_ratio,
            CASE 
                WHEN u.month IN (5,6,7,8,9,10) 
                THEN ROUND(COALESCE(u.offpeak / NULLIF(t.total_monthly, 0) * 100, 0), 2)
                ELSE NULL 
            END as summer_offpeak_ratio,
            CASE 
                WHEN u.month IN (1,2,3,4,11,12) 
                THEN ROUND(COALESCE(u.sat_midpeak / NULLIF(u.midpeak, 0) * 100, 0), 2)
                ELSE NULL 
            END as nonsummer_sat_midpeak_ratio,
            CASE 
                WHEN u.month IN (5,6,7,8,9,10) 
                THEN ROUND(COALESCE(u.sat_midpeak / NULLIF(u.midpeak, 0) * 100, 0), 2)
                ELSE NULL 
            END as summer_sat_midpeak_ratio,
            t.total_monthly,
            ROUND(COALESCE(s.summer_total / NULLIF(s.nonsummer_total, 0) * 100, 0), 2) as summer_to_nonsummer_ratio
        FROM monthly_total t
        JOIN usage_by_period u ON t.year = u.year AND t.month = u.month
        JOIN seasonal_total s ON t.year = s.year
        ORDER BY u.year, u.month
        """
        df = pd.read_sql_query(query, connection)
        all_results.append(df)
    
    # 合併所有數據
    final_df = pd.concat(all_results, ignore_index=True)
    
    # 定義特徵
    features = [
        'peak_ratio',
        'nonsummer_midpeak_ratio', 'summer_midpeak_ratio',
        'nonsummer_offpeak_ratio', 'summer_offpeak_ratio',
        'nonsummer_sat_midpeak_ratio', 'summer_sat_midpeak_ratio',
        'summer_to_nonsummer_ratio'  # 新增的特徵
    ]
    
    # 處理空值
    for feature in features:
        final_df[feature].fillna(final_df[feature].mean(), inplace=True)
    
    # 計算每個案場的平均特徵值
    site_features = final_df.groupby('site')[features].mean().reset_index()
    print("\n各案場的平均特徵值：")
    print(site_features)
    
    # 標準化數據
    X = StandardScaler().fit_transform(site_features[features])
    
    def perform_kmeans_analysis(k, X, site_features, final_df, features, output_folder, suffix=''):
        print(f"\n執行 K={k} 的分群分析...")
        
        # 對案場進行分群
        kmeans = KMeans(n_clusters=k, random_state=42)
        site_features['Cluster'] = kmeans.fit_predict(X)
        
        # 將分群結果映射回原始數據
        site_cluster_map = site_features.set_index('site')['Cluster'].to_dict()
        final_df['Cluster'] = final_df['site'].map(site_cluster_map)
        
        # 分析每個群集的特徵
        print(f"\nK={k} 各群集特徵分析：")
        cluster_analysis = site_features.groupby('Cluster')[features].mean()
        print(cluster_analysis)
        
        # 儲存分析結果
        excel_file = os.path.join(output_folder, f'kmeans_analysis_k{k}{suffix}.xlsx')
        try:
            with pd.ExcelWriter(excel_file, mode='w') as writer:
                final_df.to_excel(writer, sheet_name='Raw_Data', index=False)
                cluster_analysis.to_excel(writer, sheet_name='Cluster_Analysis')
                site_features.to_excel(writer, sheet_name='Site_Features', index=False)
        except PermissionError:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = os.path.join(output_folder, f'kmeans_analysis_k{k}{suffix}_{timestamp}.xlsx')
            with pd.ExcelWriter(excel_file, mode='w') as writer:
                final_df.to_excel(writer, sheet_name='Raw_Data', index=False)
                cluster_analysis.to_excel(writer, sheet_name='Cluster_Analysis')
                site_features.to_excel(writer, sheet_name='Site_Features', index=False)
        
        # 視覺化分群結果
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X)
        
        fig = px.scatter(
            x=X_pca[:, 0], 
            y=X_pca[:, 1],
            color=site_features['Cluster'].astype(str),
            hover_data={
                'Site': site_features['site'],
                'Peak Ratio': site_features['peak_ratio'],
                'Non-Summer Mid-peak': site_features['nonsummer_midpeak_ratio'],
                'Summer Mid-peak': site_features['summer_midpeak_ratio'],
                'Non-Summer Off-peak': site_features['nonsummer_offpeak_ratio'],
                'Summer Off-peak': site_features['summer_offpeak_ratio'],
                'Non-Summer Sat.Mid-peak': site_features['nonsummer_sat_midpeak_ratio'],
                'Summer Sat.Mid-peak': site_features['summer_sat_midpeak_ratio'],
                'Summer/Non-Summer Ratio': site_features['summer_to_nonsummer_ratio']  # 新增的特徵
            },
            title=f'案場用電模式分群結果 (K={k}) (PCA降維展示)'
        )
        
        fig.write_html(os.path.join(output_folder, f'kmeans_clusters_pca_k{k}{suffix}.html'))
        
        # 特徵分布圖
        fig = go.Figure()
        for feature in features:
            fig.add_trace(go.Box(
                y=site_features[feature],
                x=site_features['Cluster'].astype(str),
                name=feature,
                boxpoints='all'
            ))
        
        fig.update_layout(
            title=f'各群集的特徵分布 (K={k})',
            xaxis_title='群集',
            yaxis_title='比例 (%)',
            boxmode='group'
        )
        
        fig.write_html(os.path.join(output_folder, f'kmeans_feature_distribution_k{k}{suffix}.html'))
        
        return excel_file
    
    # 找最佳的K值
    max_k = min(len(site_features), 10)  # 最多分10類或案場數量
    silhouette_scores = []
    K = range(2, max_k)
    
    print("\n尋找最佳分群數量...")
    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X)
        score = silhouette_score(X, kmeans.labels_)
        silhouette_scores.append(score)
        print(f"K={k} 的輪廓係數: {score:.4f}")
    
    best_k = K[np.argmax(silhouette_scores)]
    print(f"\n最佳分群數量: {best_k}")
    
    # 執行不同K值的分析
    best_k_files = perform_kmeans_analysis(best_k, X, site_features, final_df, features, output_folder, '_best')
    k3_files = perform_kmeans_analysis(3, X, site_features, final_df, features, output_folder)
    k4_files = perform_kmeans_analysis(4, X, site_features, final_df, features, output_folder)
    
    print("\n分析完成！")

except (Exception, psycopg2.Error) as error:
    print("\n執行時發生錯誤：")
    print(f"錯誤類型: {type(error)}")
    print(f"錯誤訊息: {str(error)}")
    
finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
        print("\n資料庫連線已關閉")

