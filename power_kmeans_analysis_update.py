import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA

# ... (前面的 import 部分保持不變)

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

    # ... (中間的程式碼保持不變)

    # 更新特徵列表
    features = [
        'peak_ratio',
        'nonsummer_midpeak_ratio', 'summer_midpeak_ratio',
        'nonsummer_offpeak_ratio', 'summer_offpeak_ratio',
        'nonsummer_sat_midpeak_ratio', 'summer_sat_midpeak_ratio',
        'summer_to_nonsummer_ratio'  # 新增的特徵
    ]

    # ... (視覺化部分也需要更新)
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

# ... (其餘程式碼保持不變) 