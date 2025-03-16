import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import psycopg2
from datetime import datetime, time
import calendar
import sys

class PowerPlantAnalyzer:
    def __init__(self, db_params):
        """
        初始化分析器
        """
        try:
            # 首先測試直接連接
            print("測試資料庫連接...")
            conn = psycopg2.connect(
                dbname=db_params['database'],
                user=db_params['user'],
                password=db_params['password'],
                host=db_params['host'],
                port=db_params['port']
            )
            conn.close()
            print("資料庫連接測試成功！")
            
            # 創建 SQLAlchemy 引擎
            self.engine = create_engine(
                f'postgresql://{db_params["user"]}:{db_params["password"]}@'
                f'{db_params["host"]}:{db_params["port"]}/{db_params["database"]}'
            )
        except Exception as e:
            print(f"資料庫連接錯誤：{str(e)}")
            sys.exit(1)
    
    def is_summer_date(self, date):
        """
        判斷日期是否在夏季期間（5/16-10/15）
        """
        month = date.month
        day = date.day
        
        if month == 5:
            return day >= 16
        elif month == 10:
            return day <= 15
        else:
            return 5 < month < 10
    
    def get_power_plants_data(self, start_date, end_date, target_plants):
        """
        獲取指定時間範圍內的電廠發電數據
        """
        try:
            print(f"查詢時間範圍：{start_date} 到 {end_date}")
            
            # 構建電廠名稱的條件
            plant_conditions = " OR ".join([f"facility_name = '{plant}'" for plant in target_plants])
            
            query = f"""
            SELECT 
                datentime,
                facility_name,
                tech,
                capacity,
                used_percentage,
                CONCAT(facility_name, ' (', tech, ')') as plant_name
            FROM tw10min_capacityused
            WHERE datentime BETWEEN '{start_date}' AND '{end_date}'
            AND ({plant_conditions})
            ORDER BY datentime, facility_name
            """
            print("執行SQL查詢...")
            data = pd.read_sql(query, self.engine)
            print(f"查詢完成，獲取到 {len(data)} 筆資料")
            
            # 處理時間相關欄位
            data['datentime'] = pd.to_datetime(data['datentime'])
            data['hour'] = data['datentime'].dt.hour
            data['day_of_week'] = data['datentime'].dt.dayofweek
            data['month'] = data['datentime'].dt.month
            data['year'] = data['datentime'].dt.year
            data['is_summer'] = data['datentime'].apply(self.is_summer_date)
            
            # 添加時段分類
            data['time_period'] = data.apply(
                lambda x: self.classify_time_period(
                    x['hour'], 
                    x['day_of_week'],
                    x['is_summer']
                ),
                axis=1
            )
            
            return data
            
        except Exception as e:
            print(f"數據查詢錯誤：{str(e)}")
            sys.exit(1)
    
    def calculate_theoretical_periods(self, year, month):
        """
        計算指定年月中每種時段的理論10分鐘時段數
        """
        # 獲取該月的天數
        days_in_month = calendar.monthrange(year, month)[1]
        
        # 初始化計數器
        peak_count = 0
        mid_peak_count = 0
        off_peak_count = 0
        
        # 檢查每一天
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day)
            is_summer = self.is_summer_date(date)
            day_of_week = date.weekday()
            
            # 每小時有6個10分鐘時段
            for hour in range(24):
                period = self.classify_time_period(hour, day_of_week, is_summer)
                if period == 'peak':
                    peak_count += 6
                elif period == 'mid-peak':
                    mid_peak_count += 6
                else:  # off-peak
                    off_peak_count += 6
        
        return {
            'peak': peak_count,
            'mid-peak': mid_peak_count,
            'off-peak': off_peak_count
        }
    
    def classify_time_period(self, hour, day_of_week, is_summer):
        """
        根據時間將數據分類為peak、mid-peak或off-peak
        """
        if day_of_week == 6:  # 星期日
            return 'off-peak'
            
        if is_summer:  # 夏季
            if day_of_week == 5:  # 星期六
                return 'mid-peak' if 9 <= hour < 24 else 'off-peak'
            else:  # 平日
                if 16 <= hour < 22:
                    return 'peak'
                elif (9 <= hour < 16) or (22 <= hour < 24):
                    return 'mid-peak'
                else:
                    return 'off-peak'
        else:  # 非夏季
            if day_of_week == 5:  # 星期六
                if (6 <= hour < 11) or (14 <= hour < 24):
                    return 'mid-peak'
                else:
                    return 'off-peak'
            else:  # 平日
                if (6 <= hour < 11) or (14 <= hour < 24):
                    return 'mid-peak'
                else:
                    return 'off-peak'
    
    def plot_plant_generation(self, data, plant_name):
        """
        繪製電廠發電量圖表
        """
        # 篩選特定電廠的數據
        plant_data = data[data['plant_name'] == plant_name].copy()
        capacity = plant_data['capacity'].iloc[0]  # 獲取電廠容量
        
        plt.figure(figsize=(15, 6))
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 繪製時間序列圖
        plt.plot(plant_data['datentime'], plant_data['used_percentage'], linewidth=1)
        plt.title(f'{plant_name}\n裝置容量: {capacity:.2f} MW')
        plt.xlabel('時間')
        plt.ylabel('使用率 (%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 格式化x軸日期
        plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        plt.savefig(f'analysis_{plant_name.replace("/", "_")}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_monthly_stats(self, data):
        """
        生成月度統計表格
        """
        # 計算每個電廠每月各時段的統計數據
        monthly_stats = data.groupby(['plant_name', 'year', 'month', 'time_period']).agg({
            'used_percentage': ['mean', 'count'],
            'capacity': 'first'
        }).reset_index()
        
        # 重新命名列
        monthly_stats.columns = ['案場名稱', '年份', '月份', '時間分類', '平均使用率', '實際資料筆數', '裝置容量']
        
        # 添加理論時段數
        theoretical_periods = []
        for _, row in monthly_stats.iterrows():
            periods = self.calculate_theoretical_periods(row['年份'], row['月份'])
            theoretical_periods.append(periods[row['時間分類'].lower()])
        
        monthly_stats['理論時段數'] = theoretical_periods
        monthly_stats['資料完整率'] = (monthly_stats['實際資料筆數'] / monthly_stats['理論時段數'] * 100).round(2)
        
        # 排序
        monthly_stats = monthly_stats.sort_values(['案場名稱', '年份', '月份', '時間分類'])
        
        # 將平均使用率轉換為百分比格式
        monthly_stats['平均使用率'] = monthly_stats['平均使用率'].round(2)
        
        # 保存到CSV
        monthly_stats.to_csv('monthly_stats.csv', index=False, encoding='utf-8-sig')
        
        return monthly_stats
    
    def plot_monthly_comparison(self, data, plant_name):
        """
        繪製電廠2022和2023年各月份的發電表現比較圖
        """
        try:
            # 篩選特定電廠的數據
            plant_data = data[data['plant_name'] == plant_name].copy()
            if len(plant_data) == 0:
                print(f"警告：找不到 {plant_name} 的數據")
                return
                
            capacity = plant_data['capacity'].iloc[0]  # 獲取電廠容量
            
            # 計算每個月平均使用率
            monthly_avg = plant_data.groupby(['year', 'month'])['used_percentage'].mean().reset_index()
            
            # 創建新的圖形
            plt.figure(figsize=(15, 6))
            
            # 設定中文字體
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 繪製2022年的數據
            data_2022 = monthly_avg[monthly_avg['year'] == 2022]
            if len(data_2022) > 0:
                plt.plot(data_2022['month'], data_2022['used_percentage'], 
                        marker='o', linewidth=2, label='2022年', color='blue')
            
            # 繪製2023年的數據
            data_2023 = monthly_avg[monthly_avg['year'] == 2023]
            if len(data_2023) > 0:
                plt.plot(data_2023['month'], data_2023['used_percentage'], 
                        marker='s', linewidth=2, label='2023年', color='red')
            
            plt.title(f'{plant_name} 年度發電表現比較\n裝置容量: {capacity:.2f} MW')
            plt.xlabel('月份')
            plt.ylabel('平均使用率 (%)')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            
            # 設定x軸刻度
            plt.xticks(range(1, 13), ['1月', '2月', '3月', '4月', '5月', '6月', 
                                     '7月', '8月', '9月', '10月', '11月', '12月'])
            
            plt.tight_layout()
            
            # 確保檔案名稱正確
            filename = f'monthly_comparison_{plant_name.replace("/", "_").replace(" ", "_")}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"成功生成圖表：{filename}")
            
        except Exception as e:
            print(f"生成 {plant_name} 的月度比較圖時發生錯誤：{str(e)}")
            import traceback
            traceback.print_exc()

def main():
    # 資料庫連接參數
    db_params = {
        'host': 'localhost',
        'database': 'mogoodatabase',
        'user': 'postgres',
        'password': '1234',
        'port': '5432'
    }
    
    # 指定要分析的電廠
    target_plants = [
        '觀園',
        '台中港',
        '王功',
        '沃一風',
        '沃二風',
        '北部小水力',
        '東部小水力',
        '中部小水力',
        '南鹽光',
        '彰濱光',
        '崙尾光',
        '中威大安',
        '天英光',
        '天衝光',
        '離岸一期',
        '離岸風力台電自有',
        '離岸風力購電'
    ]
    
    try:
        # 創建分析器實例
        print("\n初始化分析器...")
        analyzer = PowerPlantAnalyzer(db_params)
        
        # 設定分析時間範圍
        start_date = '2022-01-01'
        end_date = '2023-12-31'
        
        # 獲取數據
        print("\n正在從資料庫讀取數據...")
        data = analyzer.get_power_plants_data(start_date, end_date, target_plants)
        
        # 獲取所有電廠名稱
        plant_names = data['plant_name'].unique()
        print(f"\n找到 {len(plant_names)} 個電廠：")
        for plant in sorted(plant_names):  # 按照字母順序排序顯示
            print(f"- {plant}")
        
        # 為每個電廠生成分析圖表
        print("\n開始生成發電表現圖...")
        for plant in sorted(plant_names):  # 按照字母順序處理
            print(f'正在分析 {plant}...')
            analyzer.plot_plant_generation(data, plant)
            print(f'已完成 {plant} 的分析')
        
        # 生成月度統計表格
        print("\n正在生成月度統計表格...")
        monthly_stats = analyzer.generate_monthly_stats(data)
        print("月度統計表格已保存至 monthly_stats.csv")
        
        # 生成月度比較圖
        print("\n開始生成月度比較圖...")
        for plant in comparison_plants:
            print(f'正在生成 {plant} 的月度比較圖...')
            analyzer.plot_monthly_comparison(data, plant)
            print(f'已完成 {plant} 的月度比較圖')
        
        print("\n分析完成！")
            
    except Exception as e:
        print(f'\n發生錯誤：{str(e)}')
        import traceback
        print("\n詳細錯誤信息：")
        traceback.print_exc()

if __name__ == "__main__":
    main() 