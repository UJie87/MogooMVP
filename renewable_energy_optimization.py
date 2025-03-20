import pandas as pd
import numpy as np
import pulp as plp
import os
from datetime import datetime

class RenewableEnergyOptimizer:
    def __init__(self):
        """
        初始化可再生能源組合優化器
        """
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 數據文件路徑
        self.demand_file = os.path.join(self.base_path, "D usage_analysis", "4 clustor TOU.csv")
        self.supply_file = os.path.join(self.base_path, "G3.TOU_weighted_performance", "monthly_tou_averages_2025.csv")
        
        # 約束條件（kW）
        self.constraints = {
            "s_max": 200000,  # 太陽能最大容量
            "w_max": 50000,   # 陸上風電最大容量
            "h_max": 50,      # 小水電最大容量
            "ow_max": 400000  # 離岸風電最大容量
        }
        
        # 成本係數（NTD/kW, 20年）
        self.cost_coefficients = {
            "s": 1690.96 * 5.8,    # 太陽能
            "w": 4235.91 * 5.5,    # 陸上風電
            "h": 5615.54 * 5.0,    # 小水電
            "ow": 3464.44 * 6.2    # 離岸風電
        }
        
        # 載入數據
        self.load_data()
    
    def load_data(self):
        """
        載入需求和供應數據
        """
        # 載入需求數據
        self.demand_data = pd.read_csv(self.demand_file)
        
        # 載入供應數據
        self.supply_data = pd.read_csv(self.supply_file)
    
    def calculate_renewable_target(self, annual_consumption, target_ratio, target_year, growth_rate):
        """
        計算可再生能源目標值
        
        參數:
        annual_consumption (float): 2024年年度用電量 (kWh)
        target_ratio (float): 可再生能源目標比例 (百分比)
        target_year (int): 目標年份 (2026-2050)
        growth_rate (float): 年度用電增長率 (百分比)
        
        返回:
        float: 可再生能源目標值 (kWh)
        """
        years = target_year - 2024
        target = annual_consumption * (target_ratio / 100) * (1 + growth_rate / 100) ** years
        return target
    
    def optimize_portfolio(self, site_type, annual_consumption, target_ratio, target_year, growth_rate):
        """
        優化可再生能源組合
        
        參數:
        site_type (int): 0-3 代表不同場址類型
        annual_consumption (float): 2024年年度用電量 (kWh)
        target_ratio (float): 可再生能源目標比例 (百分比)
        target_year (int): 目標年份 (2026-2050)
        growth_rate (float): 年度用電增長率 (百分比)
        
        返回:
        dict: 優化結果
        """
        # 計算可再生能源目標值
        re_target = self.calculate_renewable_target(annual_consumption, target_ratio, target_year, growth_rate)
        
        # 創建優化問題
        prob = plp.LpProblem("RenewableEnergyPortfolioOptimization", plp.LpMinimize)
        
        # 決策變數
        s_prime = plp.LpVariable("s_prime", 0, self.constraints["s_max"])  # 太陽能容量 (kW)
        w_prime = plp.LpVariable("w_prime", 0, self.constraints["w_max"])  # 陸上風電容量 (kW)
        h_prime = plp.LpVariable("h_prime", 0, self.constraints["h_max"])  # 小水電容量 (kW)
        ow_prime = plp.LpVariable("ow_prime", 0, self.constraints["ow_max"])  # 離岸風電容量 (kW)
        
        # 目標函數: 最小化總採購成本
        prob += (s_prime * self.cost_coefficients["s"] + 
                 w_prime * self.cost_coefficients["w"] + 
                 h_prime * self.cost_coefficients["h"] + 
                 ow_prime * self.cost_coefficients["ow"])
        
        # 計算實際用電需求和可再生能源供應
        total_re_used = 0
        surplus_variables = []  # 用於存儲所有的餘電變數
        
        # 處理每個月和TOU時段的供需匹配
        for _, supply_row in self.supply_data.iterrows():
            month = supply_row['month']
            tou = supply_row['tou']
            
            # 找到對應的需求數據
            demand_row = self.demand_data[(self.demand_data['month'] == month) & 
                                         (self.demand_data['tou'] == tou)]
            
            if not demand_row.empty:
                # 需求歸一化係數
                demand_factor = float(demand_row[str(site_type)].values[0])
                
                # 計算實際需求
                actual_demand = annual_consumption * demand_factor
                
                # 供應量 (kWh)
                supply = (s_prime * supply_row['SAP_kWh'] + 
                          w_prime * supply_row['WAP_kWh'] + 
                          h_prime * supply_row['HAP_kWh'] + 
                          ow_prime * supply_row['OWAP_kWh'])
                
                # 實際使用的可再生能源 = min(供應, 需求)
                # 由於我們不能在PuLP中直接使用min函數，因此使用額外的變數和約束
                actual_re_used = plp.LpVariable(f"actual_re_used_{month}_{tou}", 0, None)
                surplus = plp.LpVariable(f"surplus_{month}_{tou}", 0, None)
                
                # 記錄餘電變數
                surplus_variables.append(surplus)
                
                # 約束: actual_re_used + surplus = supply
                prob += actual_re_used + surplus == supply
                
                # 約束: actual_re_used <= actual_demand
                prob += actual_re_used <= actual_demand
                
                # 累加實際使用的可再生能源
                total_re_used += actual_re_used
        
        # 約束: 總實際使用的可再生能源必須等於可再生能源目標
        prob += total_re_used == re_target
        
        # 解決優化問題
        prob.solve()
        
        # 檢查解決方案狀態
        if plp.LpStatus[prob.status] != 'Optimal':
            return {
                "status": plp.LpStatus[prob.status],
                "message": "無法找到最佳解決方案"
            }
        
        # 計算總成本
        total_cost = (s_prime.value() * self.cost_coefficients["s"] + 
                      w_prime.value() * self.cost_coefficients["w"] + 
                      h_prime.value() * self.cost_coefficients["h"] + 
                      ow_prime.value() * self.cost_coefficients["ow"])
        
        # 計算總餘電量
        total_surplus = sum(surplus.value() for surplus in surplus_variables)
        
        # 計算總採購量 (總發電量)
        total_generation = re_target + total_surplus
        
        # 計算餘電比例
        surplus_ratio = total_surplus / total_generation if total_generation > 0 else 0
        
        # 返回結果
        return {
            "status": "最佳解決方案找到",
            "s_prime": s_prime.value(),  # 太陽能容量 (kW)
            "w_prime": w_prime.value(),  # 陸上風電容量 (kW)
            "h_prime": h_prime.value(),  # 小水電容量 (kW)
            "ow_prime": ow_prime.value(),  # 離岸風電容量 (kW)
            "total_cost": total_cost,  # 總成本 (NTD)
            "re_target": re_target,  # 可再生能源目標 (kWh)
            "unit_cost": total_cost / re_target if re_target > 0 else 0,  # 單位成本 (NTD/kWh)
            "total_surplus": total_surplus,  # 總餘電量 (kWh)
            "total_generation": total_generation,  # 總發電量 (kWh)
            "surplus_ratio": surplus_ratio  # 餘電比例
        }
    
    def run_interactive(self):
        """
        交互式運行優化程序
        """
        print("=" * 60)
        print("可再生能源組合優化程序")
        print("=" * 60)
        
        # 收集輸入參數
        print("\n目前僅支援台灣地區")
        
        # 場址類型
        print("\n請選擇場址類型:")
        print("0: 全年24/7運行的設施，季節性需求穩定")
        print("1: 辦公樓/商業中心")
        print("2: 雙班制工廠或有限運行時間的工業設施")
        print("3: 全年24/7運行的工廠，有顯著的季節性需求變化")
        
        site_type = int(input("請輸入場址類型 (0-3): "))
        if site_type not in [0, 1, 2, 3]:
            print("無效的場址類型，請選擇0-3之間的數字")
            return
        
        # 年度用電量
        annual_consumption = float(input("\n請輸入2024年年度用電量 (kWh): "))
        
        # 可再生能源目標比例
        target_ratio = float(input("\n請輸入可再生能源目標比例 (%): "))
        
        # 目標年份
        target_year = int(input("\n請輸入目標年份 (2026-2050): "))
        if target_year < 2026 or target_year > 2050:
            print("無效的目標年份，請選擇2026-2050之間的年份")
            return
        
        # 年度用電增長率
        growth_rate = float(input("\n請輸入年度用電增長率 (%): "))
        
        # 運行優化
        print("\n正在優化可再生能源組合...")
        result = self.optimize_portfolio(site_type, annual_consumption, target_ratio, target_year, growth_rate)
        
        # 顯示結果
        print("\n" + "=" * 60)
        print("優化結果")
        print("=" * 60)
        
        if result["status"] != "最佳解決方案找到":
            print(f"狀態: {result['status']}")
            print(f"訊息: {result['message']}")
            return
        
        print(f"狀態: {result['status']}")
        print(f"\n可再生能源目標: {result['re_target']:.2f} kWh")
        print("\n最佳組合:")
        print(f"太陽能 (s'): {result['s_prime']:.2f} kW")
        print(f"陸上風電 (w'): {result['w_prime']:.2f} kW")
        print(f"小水電 (h'): {result['h_prime']:.2f} kW")
        print(f"離岸風電 (ow'): {result['ow_prime']:.2f} kW")
        
        print(f"\n總採購成本: {result['total_cost']:.2f} NTD")
        print(f"單位成本: {result['unit_cost']:.2f} NTD/kWh")
        print(f"總餘電量: {result['total_surplus']:.2f} kWh")
        print(f"總發電量: {result['total_generation']:.2f} kWh")
        print(f"餘電比例: {result['surplus_ratio']:.2%}")

def main():
    optimizer = RenewableEnergyOptimizer()
    optimizer.run_interactive()

if __name__ == "__main__":
    main() 