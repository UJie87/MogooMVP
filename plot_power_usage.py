import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 設定中文字型（如果需要顯示中文）
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

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
    
    # 創建一個空的 DataFrame 來存儲所有數據
    all_data = []
    
    # 從每個摘要表格收集數據
    for table in summary_tables:
        # 從表格名稱提取公司和廠區信息
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
    
    # 創建日期列
    combined_data['date'] = pd.to_datetime(combined_data['year'].astype(str) + '-' + 
                                         combined_data['month'].astype(str) + '-01')
    
    # 設定圖表風格
    sns.set_style("whitegrid")
    plt.figure(figsize=(15, 10))
    
    # 為每個時段創建單獨的圖表
    time_periods = ['peak', 'mid-peak', 'Sat. mid-peak', 'off-peak']
    
    for period in time_periods:
        plt.figure(figsize=(15, 8))
        period_data = combined_data[combined_data['time_period'] == period]
        
        # 為每個廠區繪製一條線
        for site in period_data['site'].unique():
            site_data = period_data[period_data['site'] == site]
            plt.plot(site_data['date'], 
                    site_data['total_usage'], 
                    label=site, 
                    marker='o')
        
        plt.title(f'{period} 用電量趨勢圖')
        plt.xlabel('日期')
        plt.ylabel('用電量')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f'usage_{period}.png')
        plt.close()
    
    # 計算總用電量並繪圖
    print("正在計算總用電量...")
    total_usage = combined_data.pivot_table(
        index=['site', 'date'],
        values='total_usage',
        aggfunc='sum'
    ).reset_index()
    
    plt.figure(figsize=(15, 8))
    for site in total_usage['site'].unique():
        site_data = total_usage[total_usage['site'] == site]
        plt.plot(site_data['date'], 
                site_data['total_usage'], 
                label=site, 
                marker='o')
    
    plt.title('總用電量趨勢圖')
    plt.xlabel('日期')
    plt.ylabel('總用電量')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('total_usage.png')
    plt.close()
    
    print("圖表已生成完成！")
    print("已產生以下檔案：")
    print("1. usage_peak.png")
    print("2. usage_mid-peak.png")
    print("3. usage_Sat._mid-peak.png")
    print("4. usage_off-peak.png")
    print("5. total_usage.png")

except (Exception, psycopg2.Error) as error:
    print("\n執行時發生錯誤：")
    print(error)

finally:
    if connection:
        cursor.close()
        connection.close()
        print("\n資料庫連線已關閉") 