import pandas as pd
import os
from datetime import datetime, time

class TOUAnalyzer2025:
    def __init__(self):
        """
        初始化2025年TOU分析器
        """
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.input_file = os.path.join(self.base_path, 'combined_performance.csv')
        self.output_file = os.path.join(self.base_path, 'monthly_tou_averages_2025.csv')

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

    def analyze_tou(self):
        """
        分析2025年TOU數據
        """
        try:
            # 讀取整合後的數據
            print(f"正在讀取數據：{self.input_file}")
            df = pd.read_csv(self.input_file)
            print(f"成功讀取數據，共 {len(df)} 筆記錄")

            # 新增月份欄位
            df['month'] = df['date'].apply(lambda x: int(x.split('-')[0]))
            
            # 新增TOU時段欄位
            print("\n正在計算TOU時段...")
            df['tou'] = df.apply(self.get_tou_period, axis=1)
            
            # 顯示計算過程的範例（以1月1日為例）
            print("\n計算過程範例（1月1日）：")
            sample_day = df[df['date'] == '01-01'].copy()
            print("\n1月1日的數據：")
            print(sample_day[['date', 'time', '2025 weekday', 'tou', 'SAP', 'WAP', 'HAP', 'OWAP']].head(10))
            
            # 計算每月不同TOU時段的平均值
            print("\n正在計算月度TOU平均值...")
            monthly_averages = df.groupby(['month', 'tou'])[['SAP', 'WAP', 'HAP', 'OWAP']].mean().reset_index()
            
            # 顯示分組計算的過程
            print("\n分組計算過程：")
            for month in range(1, 13):
                month_data = df[df['month'] == month]
                print(f"\n第 {month} 月：")
                print(f"總記錄數：{len(month_data)}")
                tou_counts = month_data['tou'].value_counts()
                print("各TOU時段的記錄數：")
                print(tou_counts)
            
            # 排序結果
            monthly_averages = monthly_averages.sort_values(['month', 'tou'])
            
            # 儲存結果
            monthly_averages.to_csv(self.output_file, index=False)
            print(f"\n已將月度TOU平均值保存至：{self.output_file}")
            
            # 讀取並顯示CSV檔案的前10行
            print("\nCSV檔案內容（前10行）：")
            result_df = pd.read_csv(self.output_file)
            print(result_df.head(10))
            
            return monthly_averages
            
        except Exception as e:
            print(f"分析過程中發生錯誤：{str(e)}")
            return None

def main():
    analyzer = TOUAnalyzer2025()
    analyzer.analyze_tou()

if __name__ == "__main__":
    main() 