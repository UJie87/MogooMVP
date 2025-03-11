import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import psycopg2
from datetime import datetime
import seaborn as sns
from scipy import stats

class PowerPlantComparator:
    def __init__(self, db_params):
        """
        初始化比較器
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

    def calculate_daily_averages(self, data):
        """
        計算每個電廠的日平均值
        """
        return data.groupby(['facility_name', data['datentime'].dt.date])['used_percentage'].mean().reset_index()

    def analyze_plants(self, data):
        """
        分析並比較電廠表現
        """
        print("\n開始分析電廠表現比較...")
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 計算日平均
        daily_data = self.calculate_daily_averages(data)
        
        # 轉換為樞紐表格式，方便計算相關性
        daily_pivot = daily_data.pivot(index='datentime', 
                                     columns='facility_name', 
                                     values='used_percentage')

        # 計算移動平均
        ma_7 = daily_pivot.rolling(window=7, min_periods=1).mean()
        ma_30 = daily_pivot.rolling(window=30, min_periods=1).mean()

        # 繪製比較圖表
        self.plot_comparison(daily_pivot, ma_7, ma_30)
        
        # 計算相關性分析
        self.correlation_analysis(daily_pivot)

    def plot_comparison(self, daily_data, ma_7, ma_30):
        """
        繪製比較圖表
        """
        # 1. 日平均比較圖
        plt.figure(figsize=(15, 8))
        for column in daily_data.columns:
            plt.plot(daily_data.index, daily_data[column], 
                    label=f'{column}', linewidth=1)
        plt.title('電廠日平均發電效率比較')
        plt.xlabel('日期')
        plt.ylabel('使用率 (%)')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.show()
        
        # 2. 7天移動平均比較圖
        plt.figure(figsize=(15, 8))
        for column in ma_7.columns:
            plt.plot(ma_7.index, ma_7[column], 
                    label=f'{column}', linewidth=2)
        plt.title('電廠7天移動平均發電效率比較')
        plt.xlabel('日期')
        plt.ylabel('使用率 (%)')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.show()
        
        # 3. 30天移動平均比較圖
        plt.figure(figsize=(15, 8))
        for column in ma_30.columns:
            plt.plot(ma_30.index, ma_30[column], 
                    label=f'{column}', linewidth=2)
        plt.title('電廠30天移動平均發電效率比較')
        plt.xlabel('日期')
        plt.ylabel('使用率 (%)')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.show()

    def correlation_analysis(self, daily_data):
        """
        進行相關性分析
        """
        # 計算皮爾遜相關係數
        correlation = daily_data.corr()
        
        # 繪製相關性熱圖
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('電廠發電效率相關性分析')
        plt.tight_layout()
        plt.show()

        # 計算並顯示所有電廠對之間的相關性
        print(f"\n相關性分析結果：")
        plants = daily_data.columns
        for i in range(len(plants)):
            for j in range(i+1, len(plants)):
                plant1, plant2 = plants[i], plants[j]
                correlation_coef, p_value = stats.pearsonr(
                    daily_data[plant1].dropna(), 
                    daily_data[plant2].dropna()
                )
                print(f"\n{plant1} 與 {plant2} 的相關性：")
                print(f"皮爾遜相關係數：{correlation_coef:.4f}")
                print(f"P值：{p_value:.4f}")
        
        print(f"\n解讀：")
        print(f"- 相關係數範圍從-1到1，1表示完全正相關，-1表示完全負相關，0表示無相關")
        print(f"- P值小於0.05表示相關性具有統計顯著性")

def main():
    # 資料庫連接參數
    db_params = {
        'host': 'localhost',
        'database': 'mogoodatabase',
        'user': 'postgres',
        'password': '1234',
        'port': '5432'
    }
    
    try:
        # 創建比較器實例
        comparator = PowerPlantComparator(db_params)
        
        # 指定要比較的電廠
        facility_names = ['南鹽光', '彰濱光', '崙尾光']
        
        # 獲取數據
        data = comparator.get_plant_data(facility_names)
        
        # 進行比較分析
        comparator.analyze_plants(data)
        
    except Exception as e:
        print(f"發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 