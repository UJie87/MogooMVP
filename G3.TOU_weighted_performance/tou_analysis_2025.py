import pandas as pd
import os
from datetime import datetime, time, timedelta
import calendar

class TOUAnalyzer2025:
    def __init__(self):
        """
        初始化2025年TOU分析器
        """
        self.input_file = r'C:\Users\You Jie Tsai\Desktop\python\[G tool]-combined_performance_forstep2-3\combined_performance.csv'
        self.base_path = os.path.dirname(os.path.abspath(__file__))
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

    def calculate_monthly_hours(self, year=2025):
        """
        計算每個月份中各個TOU時段的實際小時數
        """
        monthly_hours = []
        
        for month in range(1, 13):
            # 取得該月的天數
            num_days = calendar.monthrange(year, month)[1]
            
            # 初始化該月各時段的小時數
            peak_hours = 0
            mid_peak_hours = 0
            off_peak_hours = 0
            sat_mid_peak_hours = 0
            
            for day in range(1, num_days + 1):
                # 建立日期物件
                date = datetime(year, month, day)
                weekday = date.weekday()  # 0-6, 0是週一
                is_summer = self.is_summer_season(month, day)
                
                # 星期日
                if weekday == 6:
                    off_peak_hours += 24
                    continue
                
                # 星期六
                if weekday == 5:
                    if is_summer:
                        sat_mid_peak_hours += 15  # 9:00-23:59
                        off_peak_hours += 9  # 0:00-8:59
                    else:
                        sat_mid_peak_hours += 15  # 6:00-10:59 + 14:00-23:59
                        off_peak_hours += 9  # 剩餘時間
                    continue
                
                # 平日
                if is_summer:
                    peak_hours += 6  # 16:00-21:59
                    mid_peak_hours += 8  # 9:00-15:59 + 22:00-23:59
                    off_peak_hours += 10  # 0:00-8:59
                else:
                    mid_peak_hours += 15  # 6:00-10:59 + 14:00-23:59
                    off_peak_hours += 9  # 剩餘時間
            
            # 將該月的統計加入結果
            monthly_hours.extend([
                {'month': month, 'tou': 'peak', 'theoretical_hours': peak_hours},
                {'month': month, 'tou': 'mid-peak', 'theoretical_hours': mid_peak_hours},
                {'month': month, 'tou': 'off-peak', 'theoretical_hours': off_peak_hours},
                {'month': month, 'tou': 'Sat. mid-p', 'theoretical_hours': sat_mid_peak_hours}
            ])
        
        return pd.DataFrame(monthly_hours)

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
            
            # 計算每月不同TOU時段的平均值
            print("\n正在計算月度TOU平均值...")
            monthly_averages = df.groupby(['month', 'tou'])[['SAP', 'WAP', 'HAP', 'OWAP']].mean().reset_index()
            
            # 計算理論小時數
            theoretical_hours = self.calculate_monthly_hours()
            
            # 合併平均值和理論小時數
            monthly_averages = pd.merge(monthly_averages, theoretical_hours, on=['month', 'tou'])
            
            # 計算加權值 (值 * 小時數 * 1/100)
            monthly_averages['SAP_kWh'] = monthly_averages['SAP'] * monthly_averages['theoretical_hours'] * 0.01
            monthly_averages['WAP_kWh'] = monthly_averages['WAP'] * monthly_averages['theoretical_hours'] * 0.01
            monthly_averages['HAP_kWh'] = monthly_averages['HAP'] * monthly_averages['theoretical_hours'] * 0.01
            monthly_averages['OWAP_kWh'] = monthly_averages['OWAP'] * monthly_averages['theoretical_hours'] * 0.01
            
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