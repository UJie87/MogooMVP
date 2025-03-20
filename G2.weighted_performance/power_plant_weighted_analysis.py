import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import psycopg2
from datetime import datetime

class PowerPlantAnalyzer:
    def __init__(self, db_params):
        """
        初始化分析器
        """
        try:
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
            
            self.engine = create_engine(
                f'postgresql://{db_params["user"]}:{db_params["password"]}@'
                f'{db_params["host"]}:{db_params["port"]}/{db_params["database"]}'
            )
        except Exception as e:
            print(f"資料庫連接錯誤：{str(e)}")
            raise e

    def get_plant_data(self, facility_names):
        """
        獲取指定電廠的所有歷史數據
        """
        facility_names_str = "','".join(facility_names)
        query = f"""
        SELECT 
            datentime,
            facility_name,
            tech,
            capacity,
            used_percentage
        FROM tw10min_capacityused
        WHERE facility_name IN ('{facility_names_str}')
        ORDER BY datentime
        """
        print(f"正在獲取 {', '.join(facility_names)} 的歷史數據...")
        data = pd.read_sql(query, self.engine)
        data['datentime'] = pd.to_datetime(data['datentime'])
        print(f"獲取到 {len(data)} 筆數據")
        return data

    def calculate_weighted_performance(self, data, capacities):
        """
        計算 Solar Average Performance (SAP)
        SAP 是一個加權平均值，代表太陽能電廠的整體發電效率表現
        """
        # 添加月日時間列（不含年份）
        data['month_day_time'] = data['datentime'].dt.strftime('%m-%d %H:%M')
        data['month_day'] = data['datentime'].dt.strftime('%m-%d')
        
        # 計算每個設施的實際發電量（E_facility）
        data['E_facility'] = data['used_percentage'] * data.apply(
            lambda x: capacities[x['facility_name']], axis=1) * (1/6)
        
        # 計算加權值（used_percentage * E_facility）
        data['weighted_value'] = data['used_percentage'] * data['E_facility']
        
        # 按照日期時間（不含年份）分組計算SAP
        grouped = data.groupby('month_day_time').agg({
            'weighted_value': 'sum',
            'E_facility': 'sum'
        })
        
        # 計算SAP
        grouped['SAP'] = grouped['weighted_value'] / grouped['E_facility']
        
        # 將索引（month_day_time）拆分為日期和時間
        grouped = grouped.reset_index()
        grouped[['date', 'time']] = grouped['month_day_time'].str.split(' ', expand=True)
        
        # 建立一個新的DataFrame來存儲各電廠的used_percentage
        plant_data = {}
        # 取得所有年份
        available_years = sorted(data['datentime'].dt.year.unique())
        
        # 對每個電廠和每個可用年份建立數據
        for facility in ['南鹽光', '彰濱光']:
            for year in available_years:
                facility_year_data = data[
                    (data['facility_name'] == facility) & 
                    (data['datentime'].dt.year == year)
                ].copy()
                
                # 設定索引為month_day_time以便合併
                facility_year_data = facility_year_data.set_index('month_day_time')['used_percentage']
                plant_data[f'{facility}_{year}'] = facility_year_data
        
        # 將各電廠數據合併到grouped DataFrame
        for name, series in plant_data.items():
            grouped = grouped.set_index('month_day_time')
            grouped[name] = series
            grouped = grouped.reset_index()
        
        # 建立輸出用的欄位列表
        output_columns = ['date', 'time', 'SAP']
        for facility in ['南鹽光', '彰濱光']:
            for year in available_years:
                output_columns.append(f'{facility}_{year}')
        
        # 只保留需要的欄位並重新排序
        result = grouped[output_columns]
        
        # 保存為CSV檔案
        result.to_csv('solar_average_performance.csv', index=False)
        print("\nSolar Average Performance (SAP) 數據已保存至 solar_average_performance.csv")
        print(f"可用年份：{available_years}")
        print(f"包含電廠：{'、'.join(data['facility_name'].unique())}")
        
        return grouped.set_index('month_day_time')['SAP']

    def plot_performance(self, data, capacities):
        """
        繪製發電表現圖表
        """
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 計算SAP
        sap = self.calculate_weighted_performance(data, capacities)
        
        # 圖表：案場發電效率比較
        plt.figure(figsize=(15, 8))
        
        # 使用實際數據的索引
        plot_dates = [x[:5] for x in sap.index]  # 只取月-日部分
        
        # 設定顏色映射
        colors = {'南鹽光': 'blue', '彰濱光': 'green'}
        
        # 繪製各案場數據
        for facility in data['facility_name'].unique():
            facility_data = data[data['facility_name'] == facility]
            
            # 依年份繪製數據
            for year in sorted(facility_data['datentime'].dt.year.unique()):
                year_data = facility_data[facility_data['datentime'].dt.year == year]
                if not year_data.empty:
                    # 使用每十分鐘的數據
                    ten_min_values = year_data.set_index(
                        year_data['datentime'].dt.strftime('%m-%d %H:%M')
                    )['used_percentage']
                    # 只保留月日部分用於繪圖
                    plot_index = [x[:5] for x in ten_min_values.index]
                    plt.plot(plot_index,
                            ten_min_values.values,
                            label=f'{facility} {year}',
                            color=colors[facility],
                            linewidth=1.5,
                            linestyle=':' if year > min(facility_data['datentime'].dt.year) else '-',
                            alpha=0.8)
        
        # 加入SAP線
        plt.plot(plot_dates,
                sap.values,
                color='darkred',
                linestyle='--',
                linewidth=1,
                alpha=0.7,
                label='Solar Average Performance')
        
        plt.title('太陽能電廠發電效率比較（每十分鐘數據）')
        plt.xlabel('日期')
        plt.ylabel('使用率 (%)')
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 設定x軸刻度
        plt.xticks(plot_dates[::30], plot_dates[::30], rotation=45)
        plt.tight_layout()
        plt.show()

    def check_used_percentage(self, data):
        """
        檢查used_percentage的異常值
        """
        print("\n檢查used_percentage異常值：")
        print(f"數據總筆數：{len(data)}")
        
        # 檢查大於1的值
        abnormal = data[data['used_percentage'] > 1]
        print(f"\n大於1的數據筆數：{len(abnormal)}")
        if len(abnormal) > 0:
            print("\n異常值範例（前5筆）：")
            for _, row in abnormal.head().iterrows():
                print(f"時間：{row['datentime']}, 電廠：{row['facility_name']}, used_percentage：{row['used_percentage']:.2f}")
        
        # 檢查各電廠的used_percentage分布
        print("\n各電廠used_percentage統計：")
        for facility in data['facility_name'].unique():
            facility_data = data[data['facility_name'] == facility]
            print(f"\n{facility}:")
            print(f"  最小值：{facility_data['used_percentage'].min():.4f}")
            print(f"  最大值：{facility_data['used_percentage'].max():.4f}")
            print(f"  平均值：{facility_data['used_percentage'].mean():.4f}")
            print(f"  中位數：{facility_data['used_percentage'].median():.4f}")
            print(f"  大於1的筆數：{len(facility_data[facility_data['used_percentage'] > 1])}")

    def check_specific_time(self, data, capacities, target_date):
        """
        檢查特定時間點的加權平均計算過程
        """
        # 添加月日時間列（不含年份）
        data['month_day_time'] = data['datentime'].dt.strftime('%m-%d %H:%M')
        
        # 找出目標時間的數據
        target_data = data[data['month_day_time'] == target_date]
        
        print(f"\n檢查 {target_date} 的計算過程：")
        print("\n原始數據：")
        
        # 儲存每個電廠的計算結果
        capacities_list = []
        weighted_values = []
        
        for _, row in target_data.iterrows():
            print(f"\n電廠：{row['facility_name']}")
            print(f"時間：{row['datentime']} (年份：{row['datentime'].year})")
            print(f"發電效率(used_percentage)：{row['used_percentage']:.4f}")
            print(f"容量(capacity)：{capacities[row['facility_name']]}")
            
            # 計算容量加權值
            capacity = capacities[row['facility_name']]
            capacities_list.append(capacity)
            weighted_value = row['used_percentage'] * capacity
            weighted_values.append(weighted_value)
            print(f"容量加權值 = {row['used_percentage']:.4f} * {capacity} = {weighted_value:.4f}")
        
        # 計算總和
        total_weighted_value = sum(weighted_values)
        total_capacity = sum(capacities_list)
        weighted_avg = total_weighted_value / total_capacity if total_capacity != 0 else 0
        
        print("\n最終計算：")
        print("1. 總容量計算：")
        for i, capacity in enumerate(capacities_list):
            print(f"  電廠{i+1}容量：{capacity:.4f}")
        print(f"  總容量 = {' + '.join([f'{c:.4f}' for c in capacities_list])} = {total_capacity:.4f}")
        
        print("\n2. 總加權值計算：")
        for i, weighted_value in enumerate(weighted_values):
            print(f"  電廠{i+1}加權值：{weighted_value:.4f}")
        print(f"  總加權值 = {' + '.join([f'{w:.4f}' for w in weighted_values])} = {total_weighted_value:.4f}")
        
        print("\n3. 加權平均計算：")
        print(f"加權平均 = 總加權值 / 總容量")
        print(f"        = {total_weighted_value:.4f} / {total_capacity:.4f}")
        print(f"        = {weighted_avg:.4f}")

        # 顯示該時間點所有年份的數據統計
        print("\n不同年份的數據統計：")
        for year in sorted(target_data['datentime'].dt.year.unique()):
            year_data = target_data[target_data['datentime'].dt.year == year]
            print(f"\n{year}年：")
            for facility in data['facility_name'].unique():
                facility_year_data = year_data[year_data['facility_name'] == facility]
                if not facility_year_data.empty:
                    print(f"  {facility}:")
                    print(f"    發電效率：{facility_year_data['used_percentage'].values[0]:.4f}")

def main():
    # 資料庫連接參數
    db_params = {
        'host': 'localhost',
        'database': 'mogoodatabase',
        'user': 'postgres',
        'password': '1234',
        'port': '5432'
    }
    
    # 設定電廠容量（kW）
    capacities = {
        '南鹽光': 150000,
        '彰濱光': 100000
    }
    
    try:
        # 創建分析器實例
        analyzer = PowerPlantAnalyzer(db_params)
        
        # 指定要分析的電廠
        facility_names = list(capacities.keys())
        
        # 獲取數據
        data = analyzer.get_plant_data(facility_names)
        
        # 檢查異常值
        analyzer.check_used_percentage(data)
        
        # 檢查特定時間點的計算過程
        analyzer.check_specific_time(data, capacities, '03-02 12:00')
        
        # 繪製圖表
        analyzer.plot_performance(data, capacities)
        
    except Exception as e:
        print(f"發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 