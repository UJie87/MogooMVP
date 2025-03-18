import psycopg2
from psycopg2 import Error
import pandas as pd

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

    print("開始處理...")

    # 1. 先查詢有哪些不同的公司和廠區組合
    cursor.execute("""
        SELECT DISTINCT company, site 
        FROM eleconsume_twstat 
        ORDER BY company, site
    """)
    company_sites = cursor.fetchall()
    print("\n找到的公司和廠區組合：")
    for comp, site in company_sites:
        print(f"公司: {comp}, 廠區: {site}")

    # 2. 為每個公司和廠區建立摘要表
    for company, site in company_sites:
        table_name = f"summary_{company}_{site}".lower().replace(' ', '_')
        print(f"\n處理 {company} - {site}")
        
        # 建立摘要表
        create_table_sql = f"""
        DROP TABLE IF EXISTS {table_name};
        CREATE TABLE {table_name} (
            year INTEGER,
            month INTEGER,
            time_period VARCHAR(20),
            total_usage DECIMAL(20,2),
            PRIMARY KEY (year, month, time_period)
        );
        """
        cursor.execute(create_table_sql)
        print(f"已建立表格 {table_name}")
        
        # 插入資料
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
        ORDER BY year, month, time_period;
        """
        cursor.execute(insert_data_sql, (company, site))
        
        # 顯示新建表格的資料預覽
        cursor.execute(f"""
            SELECT * FROM {table_name} 
            ORDER BY year, month, time_period 
            LIMIT 5
        """)
        print(f"\n{table_name} 的前5筆資料：")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    # 提交事務
    connection.commit()
    print("\n所有表格建立和資料更新完成！")

except (Exception, Error) as error:
    print("\n執行時發生錯誤：")
    print(f"錯誤類型: {type(error)}")
    print(f"錯誤訊息: {str(error)}")
    connection.rollback()

finally:
    if connection:
        cursor.close()
        connection.close()
        print("\n資料庫連線已關閉") 