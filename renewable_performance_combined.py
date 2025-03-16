import pandas as pd
import os
from datetime import datetime, time

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
        self.tou_output_file = os.path.join(self.base_path, 'monthly_tou_averages_2025.csv')
        
        # 英文星期對照表
        self.weekday_mapping = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday'
        }

    def is_summer_season(self, month, day):
        """
        判斷是否為夏季時段 (5/16-10/15)
        """
        if month == 5:
            return day >= 16
        elif month == 10:
            return day <= 15
        else:
            return 5 < month < 10

    def get_tou_period(self, row):
        """
        根據日期、時間和星期判斷TOU時段
        """
        # 解析時間
        hour = int(row['time'].split(':')[0])
        minute = int(row['time'].split(':')[1])
        current_time = time(hour, minute)
        
        # 解析日期
        month = int(row['date'].split('-')[0])
        day = int(row['date'].split('-')[1])
        
        # 獲取星期
        weekday = row['2025 weekday']
        is_summer = self.is_summer_season(month, day)

        # 星期日
        if weekday == 'Sunday':
            return 'off-peak'
        
        # 星期六
        if weekday == 'Saturday':
            if is_summer:
                if time(9,0) <= current_time <= time(23,59):
                    return 'Sat. mid-p'
                else:
                    return 'off-peak'
            else:
                if (time(6,0) <= current_time <= time(10,59)) or \
                   (time(14,0) <= current_time <= time(23,59)):
                    return 'Sat. mid-p'
                else:
                    return 'off-peak'
        
        # 平日
        if is_summer:
            if time(16,0) <= current_time <= time(21,59):
                return 'peak'
            elif (time(9,0) <= current_time <= time(15,59)) or \
                 (time(22,0) <= current_time <= time(23,59)):
                return 'mid-peak'
            else:
                return 'off-peak'
        else:
            if (time(6,0) <= current_time <= time(10,59)) or \
               (time(14,0) <= current_time <= time(23,59)):
                return 'mid-peak'
            else:
                return 'off-peak'

    def calculate_monthly_tou_averages(self, df):
        """
        計算每月不同TOU時段的平均值
        """
        # 新增月份欄位
        df['month'] = df['date'].apply(lambda x: int(x.split('-')[0]))
        
        # 新增TOU時段欄位
        df['tou'] = df.apply(self.get_tou_period, axis=1)
        
        # 計算每月每個TOU時段的平均值
        monthly_averages = df.groupby(['month', 'tou'])[['SAP', 'WAP', 'HAP', 'OWAP']].mean().reset_index()
        
        # 排序結果
        monthly_averages = monthly_averages.sort_values(['month', 'tou'])
        
        # 儲存結果
        monthly_averages.to_csv(self.tou_output_file, index=False)
        print(f"\n已將月度TOU平均值保存至：{self.tou_output_file}")
        print("\n資料預覽：")
        print(monthly_averages.head(10))
        
        return monthly_averages

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

    def add_weekdays_for_years(self, df, start_year=2025, end_year=2050):
        """
        增加指定年份範圍的星期欄位
        """
        print(f"\n正在新增 {start_year}-{end_year} 年的星期資訊...")
        
        for year in range(start_year, end_year + 1):
            # 將 MM-DD 格式轉換為 YYYY-MM-DD 格式
            dates = pd.to_datetime(f'{year}-' + df['date'])
            # 獲取星期幾（0-6，0代表星期一）
            weekdays = dates.dt.weekday
            # 轉換為英文星期並加入年份
            column_name = f'{year} weekday'
            df[column_name] = weekdays.map(self.weekday_mapping)
            print(f"已新增 {column_name} 欄位")
            
        return df

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

        # 增加2025年的星期欄位
        result = self.add_weekdays_for_years(result, start_year=2025, end_year=2025)
        
        # 計算月度TOU平均值
        self.calculate_monthly_tou_averages(result)

        return result

    def save_combined_data(self, df):
        """
        保存整合後的數據
        """
        try:
            df.to_csv(self.output_file, index=False)
            print(f"\n已成功保存整合數據至：{self.output_file}")
            print("\n資料預覽（前5筆資料的部分欄位）：")
            preview_columns = ['date', 'time', 'SAP', 'WAP', 'HAP', 'OWAP', '2025 weekday']
            print(df[preview_columns].head())
            print(f"\n總資料筆數：{len(df)}")
            print(f"總欄位數：{len(df.columns)}")
            
            # 顯示所有欄位名稱
            print("\n所有欄位：")
            print(df.columns.tolist())
            
            # 顯示基本統計資訊
            print("\n發電效能統計資訊：")
            print(df[['SAP', 'WAP', 'HAP', 'OWAP']].describe())
            
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