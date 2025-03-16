import pandas as pd
import os
from datetime import datetime

class RenewablePerformanceCombiner:
    def __init__(self):
        """
        初始化再生能源效能整合器
        """
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.source_files = {
            'SAP': os.path.join(self.base_path, 'solar_average_performance.csv'),
            'WAP': os.path.join(self.base_path, 'wind_average_performance.csv'),
            'HAP': os.path.join(self.base_path, 'hydro_average_performance.csv'),
            'OWAP': os.path.join(self.base_path, 'offshore_wind_average_performance.csv')
        }
        self.output_file = os.path.join(self.base_path, 'combined_performance.csv')

    def read_performance_data(self, file_path, performance_type):
        """
        讀取特定類型的發電效能數據
        """
        try:
            print(f"正在讀取 {performance_type} 數據...")
            df = pd.read_csv(file_path)
            print(f"成功讀取 {performance_type} 數據，欄位：{df.columns.tolist()}")
            
            # 確保必要的欄位存在
            required_columns = ['date', 'time', performance_type]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"警告：{file_path} 缺少必要的欄位：{missing_columns}")
                return None
            
            # 只保留需要的欄位並處理遺失值
            result_df = df[required_columns].copy()
            
            # 將遺失值填充為0
            result_df[performance_type] = result_df[performance_type].fillna(0)
            
            print(f"{performance_type} 數據預覽：")
            print(result_df.head(2))
            print(f"{performance_type} 統計資訊：")
            print(result_df[performance_type].describe())
            print()
            
            return result_df
            
        except Exception as e:
            print(f"讀取 {performance_type} 數據時發生錯誤：{str(e)}")
            return None

    def combine_performance_data(self):
        """
        整合所有類型的發電效能數據
        """
        # 讀取所有數據
        dataframes = {}
        for performance_type, file_path in self.source_files.items():
            if os.path.exists(file_path):
                df = self.read_performance_data(file_path, performance_type)
                if df is not None:
                    dataframes[performance_type] = df
            else:
                print(f"警告：找不到檔案 {file_path}")

        if not dataframes:
            print("錯誤：沒有成功讀取任何數據")
            return None

        # 使用第一個數據框作為基礎
        base_df = next(iter(dataframes.values()))
        result = base_df[['date', 'time']].copy()
        print(f"\n使用 {next(iter(dataframes.keys()))} 的日期時間作為基準")

        # 加入每種類型的效能數據
        for performance_type, df in dataframes.items():
            result[performance_type] = df[performance_type]
            print(f"已加入 {performance_type} 數據")

        return result

    def save_combined_data(self, df):
        """
        保存整合後的數據
        """
        try:
            df.to_csv(self.output_file, index=False)
            print(f"\n已成功保存整合數據至：{self.output_file}")
            print("\n資料預覽：")
            print(df.head())
            print(f"\n總資料筆數：{len(df)}")
            
            # 顯示基本統計資訊
            print("\n基本統計資訊：")
            print(df.describe())
            
            # 檢查是否有遺失值
            null_counts = df.isnull().sum()
            if null_counts.any():
                print("\n遺失值統計：")
                print(null_counts[null_counts > 0])
                
        except Exception as e:
            print(f"保存數據時發生錯誤：{str(e)}")

    def run(self):
        """
        執行整個整合流程
        """
        print("開始整合再生能源發電效能數據...")
        print("="*50)
        
        # 整合數據
        combined_df = self.combine_performance_data()
        if combined_df is not None:
            self.save_combined_data(combined_df)

def main():
    combiner = RenewablePerformanceCombiner()
    combiner.run()

if __name__ == "__main__":
    main() 