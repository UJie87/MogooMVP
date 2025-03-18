import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# 創建資料夾來存放圖表
output_folder = "power_usage_plots"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"已創建資料夾：{os.path.abspath(output_folder)}")

try:
    # 建立資料庫連線
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="mogoodatabase",
        user="postgres",
        password="1234"
    )
    
    # 獲取所有摘要表格名稱
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'summary_%'
    """)
    summary_tables = [table[0] for table in cursor.fetchall()]
    
    # 收集所有數據
    all_data = []
    for table in summary_tables:
        company_site = table.replace('summary_', '')
        query = f"""
        SELECT 
            year, 
            month, 
            time_period, 
            total_usage,
            '{company_site}' as site
        FROM {table}
        ORDER BY year, month, time_period
        """
        df = pd.read_sql_query(query, connection)
        all_data.append(df)
    
    # 合併所有數據
    combined_data = pd.concat(all_data, ignore_index=True)
    combined_data['date'] = pd.to_datetime(combined_data['year'].astype(str) + '-' + 
                                         combined_data['month'].astype(str) + '-01')

    # 創建互動式圖表
    time_periods = ['peak', 'mid-peak', 'Sat. mid-peak', 'off-peak']
    
    # 為每個時段創建單獨的圖表
    for period in time_periods:
        period_data = combined_data[combined_data['time_period'] == period]
        
        fig = go.Figure()
        
        for site in period_data['site'].unique():
            site_data = period_data[period_data['site'] == site]
            
            fig.add_trace(go.Scatter(
                x=site_data['date'],
                y=site_data['total_usage'],
                name=site,
                mode='lines+markers',
                hovertemplate="""
                廠區: %{text}<br>
                日期: %{x}<br>
                用電量: %{y:.2f}<br>
                <extra></extra>
                """,
                text=[site] * len(site_data)
            ))
        
        fig.update_layout(
            title=f'{period} 用電量趨勢圖',
            xaxis_title='日期',
            yaxis_title='用電量',
            hovermode='x unified',
            width=1200,
            height=800
        )
        
        # 儲存為互動式HTML檔案
        output_file = os.path.join(output_folder, f'interactive_usage_{period}.html')
        fig.write_html(output_file)
    
    # 創建總用電量圖表
    print("正在計算總用電量...")
    total_usage = combined_data.pivot_table(
        index=['site', 'date'],
        values='total_usage',
        aggfunc='sum'
    ).reset_index()
    
    fig_total = go.Figure()
    
    for site in total_usage['site'].unique():
        site_data = total_usage[total_usage['site'] == site]
        
        fig_total.add_trace(go.Scatter(
            x=site_data['date'],
            y=site_data['total_usage'],
            name=site,
            mode='lines+markers',
            hovertemplate="""
            廠區: %{text}<br>
            日期: %{x}<br>
            總用電量: %{y:.2f}<br>
            <extra></extra>
            """,
            text=[site] * len(site_data)
        ))
    
    fig_total.update_layout(
        title='總用電量趨勢圖',
        xaxis_title='日期',
        yaxis_title='總用電量',
        hovermode='x unified',
        width=1200,
        height=800
    )
    
    # 儲存總用電量圖表
    total_output_file = os.path.join(output_folder, 'interactive_total_usage.html')
    fig_total.write_html(total_output_file)
    
    print("\n互動式圖表已生成完成！")
    print(f"\n所有圖表都已儲存在資料夾：{os.path.abspath(output_folder)}")
    print("\n已產生以下檔案：")
    for period in time_periods:
        print(f"- interactive_usage_{period}.html")
    print("- interactive_total_usage.html")

except (Exception, psycopg2.Error) as error:
    print("\n執行時發生錯誤：")
    print(error)

finally:
    if connection:
        cursor.close()
        connection.close()
        print("\n資料庫連線已關閉") 