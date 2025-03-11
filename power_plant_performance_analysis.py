import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import psycopg2
from datetime import datetime
from statsmodels.tsa.seasonal import seasonal_decompose

class PowerPlantPerformanceAnalyzer:
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
            raise e

    def get_plant_data(self, facility_name):
        """
        獲取指定電廠的所有歷史數據
        """
        query = f"""
        SELECT 
            datentime,
            facility_name,
            tech,
            capacity,
            used_percentage
        FROM tw10min_capacityused
        WHERE facility_name = '{facility_name}'
        ORDER BY datentime
        """
        print(f"正在獲取 {facility_name} 的歷史數據...")
        data = pd.read_sql(query, self.engine)
        data['datentime'] = pd.to_datetime(data['datentime'])
        print(f"獲取到 {len(data)} 筆數據")
        return data

    def analyze_performance(self, data):
        """
        分析電廠在不同時間尺度的發電表現
        """
        print("\n開始分析發電表現...")
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 計算每日平均
        daily_avg = data.groupby(data['datentime'].dt.date)['used_percentage'].mean()
        print(f"日平均數據點數：{len(daily_avg)}")
        
        # 2. 計算每月平均
        monthly_avg = data.groupby([data['datentime'].dt.year, 
                                  data['datentime'].dt.month])['used_percentage'].mean()
        print(f"月平均數據點數：{len(monthly_avg)}")
        
        # 3. 計算7天移動平均
        daily_ma_7 = daily_avg.rolling(window=7, min_periods=1).mean()
        
        # 4. 計算30天移動平均
        daily_ma_30 = daily_avg.rolling(window=30, min_periods=1).mean()
        
        # 5. 季節性分解
        # 將daily_avg轉換為時間序列格式
        ts_data = pd.Series(daily_avg.values, index=pd.to_datetime(daily_avg.index))
        
        # 使用較短的週期進行季節性分解
        try:
            decomposition = seasonal_decompose(ts_data, period=30, extrapolate_trend='freq')
            has_decomposition = True
        except Exception as e:
            print(f"季節性分解失敗：{str(e)}")
            has_decomposition = False
        
        # 繪製圖表
        self.plot_analysis_results(data['facility_name'].iloc[0],
                                 daily_avg, monthly_avg,
                                 daily_ma_7, daily_ma_30,
                                 decomposition if has_decomposition else None)

    def plot_analysis_results(self, facility_name, daily_avg, monthly_avg,
                            daily_ma_7, daily_ma_30, decomposition):
        """
        繪製分析結果圖表
        """
        # 1. 日平均和移動平均
        plt.figure(figsize=(15, 8))
        plt.plot(daily_avg.index, daily_avg.values, label='日平均', alpha=0.5)
        plt.plot(daily_ma_7.index, daily_ma_7.values, label='7天移動平均', linewidth=2)
        plt.plot(daily_ma_30.index, daily_ma_30.values, label='30天移動平均', linewidth=2)
        plt.title(f'{facility_name} 日平均發電表現與移動平均')
        plt.xlabel('日期')
        plt.ylabel('使用率 (%)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

        # 2. 月平均
        plt.figure(figsize=(15, 6))
        monthly_avg.plot(kind='bar')
        plt.title(f'{facility_name} 月平均發電表現')
        plt.xlabel('年-月')
        plt.ylabel('使用率 (%)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        # 3. 季節性分解
        if decomposition is not None:
            plt.figure(figsize=(15, 12))
            
            plt.subplot(411)
            plt.plot(decomposition.observed)
            plt.title('原始數據')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(412)
            plt.plot(decomposition.trend)
            plt.title('趨勢')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(413)
            plt.plot(decomposition.seasonal)
            plt.title('季節性')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(414)
            plt.plot(decomposition.resid)
            plt.title('殘差')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()

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
        # 創建分析器實例
        analyzer = PowerPlantPerformanceAnalyzer(db_params)
        
        # 獲取崙尾光電的數據
        facility_name = '崙尾光'
        data = analyzer.get_plant_data(facility_name)
        
        # 分析發電表現
        analyzer.analyze_performance(data)
        
    except Exception as e:
        print(f"發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 