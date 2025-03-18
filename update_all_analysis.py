import psycopg2
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

def refresh_summary_tables(cursor, connection):
    """重新建立所有摘要表"""
    print("開始更新摘要表...")
    
    # 1. 獲取所有公司和廠區的組合
    cursor.execute("""
        SELECT DISTINCT company, site 
        FROM eleconsume_twstat 
        ORDER BY company, site
    """)
    company_sites = cursor.fetchall()
    
    # 2. 為每個組合重新建立摘要表
    for company, site in company_sites:
        table_name = f"summary_{company}_{site}".lower().replace(' ', '_')
        print(f"\n更新 {company} - {site} 的摘要表...")
        
        # 刪除舊的摘要表（如果存在）
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # 建立新的摘要表
        create_table_sql = f"""
        CREATE TABLE {table_name} (
            year INTEGER,
            month INTEGER,
            time_period VARCHAR(20),
            total_usage DECIMAL(20,2),
            PRIMARY KEY (year, month, time_period)
        )
        """
        cursor.execute(create_table_sql)
        
        # 插入最新數據
        insert_data_sql = f"""
        INSERT INTO {table_name} (year, month, time_period, total_usage)
        SELECT 
            year,
            month,
            time_period,
            COALESCE(SUM(usage), 0) as total_usage
        FROM eleconsume_twstat
        WHERE company = %s AND site = %s
        GROUP BY year, month, time_period
        ORDER BY year, month, time_period
        """
        cursor.execute(insert_data_sql, (company, site))
    
    connection.commit()
    print("\n所有摘要表更新完成！")

def create_interactive_plots(cursor, output_folder):
    """建立互動式圖表"""
    print("\n開始建立互動式圖表...")
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已創建圖表資料夾：{os.path.abspath(output_folder)}")
    
    # 收集所有數據
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'summary_%'
    """)
    summary_tables = [table[0] for table in cursor.fetchall()]
    
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
    
    combined_data = pd.concat(all_data, ignore_index=True)
    combined_data['date'] = pd.to_datetime(combined_data['year'].astype(str) + '-' + 
                                         combined_data['month'].astype(str) + '-01')
    
    # 建立各時段圖表
    time_periods = ['peak', 'mid-peak', 'Sat. mid-peak', 'off-peak']
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
        
        output_file = os.path.join(output_folder, f'interactive_usage_{period}.html')
        fig.write_html(output_file)
    
    # 建立總用電量圖表
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
    
    total_output_file = os.path.join(output_folder, 'interactive_total_usage.html')
    fig_total.write_html(total_output_file)
    
    print("所有圖表更新完成！")

# 主程式
if __name__ == "__main__":
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
        
        # 設定輸出資料夾
        output_folder = "power_usage_plots"
        
        # 1. 更新所有摘要表
        refresh_summary_tables(cursor, connection)
        
        # 2. 重新建立所有圖表
        create_interactive_plots(cursor, output_folder)
        
        print(f"\n所有更新完成！圖表已儲存在：{os.path.abspath(output_folder)}")
        
    except (Exception, psycopg2.Error) as error:
        print("\n執行時發生錯誤：")
        print(error)
        if connection:
            connection.rollback()
    
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("\n資料庫連線已關閉") 