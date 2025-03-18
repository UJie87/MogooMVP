import psycopg2
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go

# 設定時間戳記
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"開始執行時間：{timestamp}")

# 確保輸出資料夾存在
output_folder = "power_usage_plots"
os.makedirs(output_folder, exist_ok=True)
print(f"輸出資料夾路徑：{os.path.abspath(output_folder)}")

def calculate_ratios(cursor, output_folder):
    print("開始計算用電比例...")
    
    # 獲取所有摘要表格
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'summary_%'
    """)
    summary_tables = [table[0] for table in cursor.fetchall()]
    
    all_results = []
    
    for table in summary_tables:
        site_name = table.replace('summary_', '')
        print(f"\n處理 {site_name} 的數據...")
        
        # 獲取該站點的所有數據
        query = f"""
        WITH monthly_total AS (
            SELECT year, month, SUM(total_usage) as total_monthly
            FROM {table}
            GROUP BY year, month
        ),
        peak_usage AS (
            SELECT year, month, total_usage as peak
            FROM {table}
            WHERE time_period = 'peak'
        ),
        midpeak_usage AS (
            SELECT year, month, total_usage as midpeak
            FROM {table}
            WHERE time_period = 'mid-peak'
        ),
        offpeak_usage AS (
            SELECT year, month, total_usage as offpeak
            FROM {table}
            WHERE time_period = 'off-peak'
        ),
        sat_midpeak_usage AS (
            SELECT year, month, total_usage as sat_midpeak
            FROM {table}
            WHERE time_period = 'Sat. mid-peak'
        )
        SELECT 
            t.year,
            t.month,
            '{site_name}' as site,
            ROUND(COALESCE(p.peak / t.total_monthly * 100, 0), 2) as peak_ratio,
            ROUND(COALESCE(m.midpeak / NULLIF(p.peak, 0) * 100, 0), 2) as midpeak_to_peak_ratio,
            ROUND(COALESCE(o.offpeak / t.total_monthly * 100, 0), 2) as offpeak_ratio,
            ROUND(COALESCE(s.sat_midpeak / NULLIF(m.midpeak, 0) * 100, 0), 2) as sat_midpeak_to_midpeak_ratio
        FROM monthly_total t
        LEFT JOIN peak_usage p ON t.year = p.year AND t.month = p.month
        LEFT JOIN midpeak_usage m ON t.year = m.year AND t.month = m.month
        LEFT JOIN offpeak_usage o ON t.year = o.year AND t.month = o.month
        LEFT JOIN sat_midpeak_usage s ON t.year = s.year AND t.month = s.month
        ORDER BY t.year, t.month
        """
        
        df = pd.read_sql_query(query, connection)
        all_results.append(df)
    
    # 合併所有結果
    final_df = pd.concat(all_results, ignore_index=True)
    
    # 格式化輸出
    print("\n=== 用電比例分析結果 ===")
    pd.set_option('display.max_rows', None)
    pd.set_option('display.float_format', lambda x: '%.2f' % x)
    
    # 顯示結果
    print("\n各站點月度用電比例：")
    print(final_df)
    
    # 儲存為Excel檔案
    excel_file = os.path.join(output_folder, f'usage_ratios_{timestamp}.xlsx')
    final_df.to_excel(excel_file, index=False)
    print(f"\n已儲存 Excel 檔案：{excel_file}")
    
    return final_df

try:
    # 建立資料庫連線
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="mogoodatabase",
        user="postgres",
        password="1234"
    )
    cursor = connection.cursor()
    
    # 計算比例
    results = calculate_ratios(cursor, output_folder)
    
    # 為不同比例建立圖表
    ratios = {
        'peak_ratio': '尖峰用電比例 (%)',
        'midpeak_to_peak_ratio': 'Mid-peak/Peak 比例 (%)',
        'offpeak_ratio': 'Off-peak/Total 比例 (%)',
        'sat_midpeak_to_midpeak_ratio': 'Sat. Mid-peak/Mid-peak 比例 (%)'
    }
    
    for ratio_col, ratio_name in ratios.items():
        fig = go.Figure()
        
        for site in results['site'].unique():
            site_data = results[results['site'] == site]
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(site_data['year'].astype(str) + '-' + 
                               site_data['month'].astype(str) + '-01'),
                y=site_data[ratio_col],
                name=site,
                mode='lines+markers',
                hovertemplate="""
                廠區: %{text}<br>
                日期: %{x}<br>
                比例: %{y:.2f}%<br>
                <extra></extra>
                """,
                text=[site] * len(site_data)
            ))
        
        fig.update_layout(
            title=ratio_name,
            xaxis_title='日期',
            yaxis_title='比例 (%)',
            hovermode='x unified',
            width=1200,
            height=800
        )
        
        # 儲存圖表
        html_file = os.path.join(output_folder, f'ratio_{ratio_col}_{timestamp}.html')
        fig.write_html(html_file)
        print(f"已生成圖表：{html_file}")

except (Exception, psycopg2.Error) as error:
    print("\n執行時發生錯誤：")
    print(f"錯誤類型: {type(error)}")
    print(f"錯誤訊息: {str(error)}")
    
finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
        print("\n資料庫連線已關閉")

print(f"\n請檢查輸出資料夾：{os.path.abspath(output_folder)}") 