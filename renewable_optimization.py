import pandas as pd
import numpy as np
from scipy.optimize import minimize
import os
import time
import shutil
from datetime import datetime

class RenewableOptimizer:
    def __init__(self):
        self.SOLAR_COST = 1690.96 * 5.8
        self.WIND_COST = 4235.91 * 5.5
        self.HYDRO_COST = 5615.54 * 5
        self.OFFSHORE_WIND_COST = 3464.44 * 6.2
        
        # Create a temporary directory for file copies
        self.temp_dir = self._create_temp_dir()
        
        # Load data with retry
        max_retries = 3
        for i in range(max_retries):
            try:
                self.load_data()
                break
            except Exception as e:
                if i < max_retries - 1:
                    print(f"Error accessing files, retrying in 2 seconds... ({i+1}/{max_retries})")
                    print(f"Error: {str(e)}")
                    time.sleep(2)
                else:
                    print("Failed to access files after multiple attempts.")
                    print("Please ensure the Excel and CSV files are not open in other programs")
                    print("and that OneDrive sync is complete.")
                    raise

    def _create_temp_dir(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(base_path, "temp_data_" + 
                               datetime.now().strftime("%Y%m%d_%H%M%S"))
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

    def _copy_file(self, src_file, prefix):
        filename = os.path.basename(src_file)
        dst_file = os.path.join(self.temp_dir, f"{prefix}_{filename}")
        try:
            shutil.copy2(src_file, dst_file)
            print(f"Successfully copied {src_file} to {dst_file}")
            return dst_file
        except Exception as e:
            print(f"Error copying {src_file}: {str(e)}")
            raise

    def load_data(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Copy and load demand profiles
        demand_src = os.path.normpath(os.path.join(base_path, 
                                r"[D]usage_analysis", 
                                r"4 clustor TOU.xlsx"))
        print(f"Copying demand data from: {demand_src}")
        demand_file = self._copy_file(demand_src, "demand")
        
        try:
            self.demand_profiles = pd.read_excel(demand_file, engine='openpyxl')
            print("Successfully loaded demand data")
        except Exception as e:
            print(f"Error loading demand file: {str(e)}")
            raise
        
        # Copy and load supply profiles
        supply_src = os.path.normpath(os.path.join(base_path, 
                                r"[G]3.TOU_weighted_performance", 
                                r"monthly_tou_averages_2025.csv"))
        print(f"Copying supply data from: {supply_src}")
        if not os.path.exists(supply_src):
            print(f"Supply file not found at: {supply_src}")
            raise FileNotFoundError(f"Supply file not found at: {supply_src}")
                
        supply_file = self._copy_file(supply_src, "supply")
        
        try:
            self.supply_profiles = pd.read_csv(supply_file)
            print("Successfully loaded supply data")
        except Exception as e:
            print(f"Error loading supply file: {str(e)}")
            raise

    def calculate_re_target(self, base_consumption, target_ratio, growth_rate, target_year):
        years = target_year - 2024
        return base_consumption * target_ratio * (1 + growth_rate) ** years

    def get_demand_profile(self, site_type, annual_consumption):
        # Get the normalized profile for the selected site type
        profile = self.demand_profiles[self.demand_profiles['site_type'] == site_type]
        return profile * annual_consumption

    def objective_function(self, x, *args):
        solar_cap, wind_cap, hydro_cap, offshore_wind_cap = x
        return (solar_cap * self.SOLAR_COST + 
                wind_cap * self.WIND_COST + 
                hydro_cap * self.HYDRO_COST + 
                offshore_wind_cap * self.OFFSHORE_WIND_COST)

    def calculate_actual_re(self, x, demand):
        solar_cap, wind_cap, hydro_cap, offshore_wind_cap = x
        
        # Calculate total supply for each period
        supply = (solar_cap * self.supply_profiles['SAP_kWh'] +
                 wind_cap * self.supply_profiles['WAP_kWh'] +
                 hydro_cap * self.supply_profiles['HAP_kWh'] +
                 offshore_wind_cap * self.supply_profiles['OWAP_kWh'])
        
        # Calculate actual RE used and surplus
        actual_re = np.minimum(supply, demand)
        surplus = np.maximum(0, supply - demand)
        
        return actual_re.sum(), surplus

    def constraint_re_target(self, x, *args):
        demand, re_target = args
        actual_re, _ = self.calculate_actual_re(x, demand)
        return actual_re - re_target

    def optimize(self, site_type, annual_consumption, target_ratio, target_year, growth_rate):
        # Calculate RE target
        re_target = self.calculate_re_target(annual_consumption, target_ratio, 
                                           growth_rate, target_year)
        
        # Get demand profile
        demand = self.get_demand_profile(site_type, annual_consumption)
        
        # Define bounds for each technology
        bounds = [(0, 200000),    # Solar
                 (0, 50000),      # Onshore wind
                 (0, 50),         # Hydro
                 (0, 400000)]     # Offshore wind
        
        # Initial guess
        x0 = [100000, 25000, 25, 200000]
        
        # Optimization
        constraints = [{'type': 'eq', 
                       'fun': self.constraint_re_target,
                       'args': (demand, re_target)}]
        
        result = minimize(self.objective_function, x0, 
                        constraints=constraints,
                        bounds=bounds,
                        method='SLSQP')
        
        if result.success:
            solar, wind, hydro, offshore = result.x
            cost = result.fun
            actual_re, surplus = self.calculate_actual_re(result.x, demand)
            
            return {
                'solar_capacity': solar,
                'wind_capacity': wind,
                'hydro_capacity': hydro,
                'offshore_wind_capacity': offshore,
                'total_cost': cost,
                'actual_re_generated': actual_re,
                're_target': re_target,
                'surplus': surplus.sum()
            }
        else:
            raise Exception("Optimization failed: " + result.message)

    def __del__(self):
        # Cleanup temporary files
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {str(e)}")

def main():
    # For testing purposes, use some example values
    site_type = 0  # 24/7 year-round facility
    annual_consumption = 1000000  # 1 million kWh
    target_ratio = 0.3  # 30% renewable
    target_year = 2030
    growth_rate = 0.05  # 5% annual growth
    
    try:
        optimizer = RenewableOptimizer()
        result = optimizer.optimize(site_type, annual_consumption, 
                                 target_ratio, target_year, growth_rate)
        
        print("\nRenewable Energy Portfolio Optimization Program")
        print("=============================================")
        print("\nInput Parameters:")
        print(f"Site Type: {site_type} (24/7 year-round facility)")
        print(f"Annual Consumption (2024): {annual_consumption:,.0f} kWh")
        print(f"RE Target Ratio: {target_ratio:.1%}")
        print(f"Target Year: {target_year}")
        print(f"Growth Rate: {growth_rate:.1%}")
        
        print("\nOptimization Results:")
        print("====================")
        print(f"\nOptimal Capacity Mix:")
        print(f"Solar: {result['solar_capacity']:,.2f} kW")
        print(f"Onshore Wind: {result['wind_capacity']:,.2f} kW")
        print(f"Small Hydro: {result['hydro_capacity']:,.2f} kW")
        print(f"Offshore Wind: {result['offshore_wind_capacity']:,.2f} kW")
        
        print(f"\nFinancial Summary:")
        print(f"Total Investment Cost: ${result['total_cost']:,.2f}")
        
        print(f"\nEnergy Summary:")
        print(f"RE Target: {result['re_target']:,.2f} kWh")
        print(f"Actual RE Generated: {result['actual_re_generated']:,.2f} kWh")
        print(f"Surplus Generation: {result['surplus']:,.2f} kWh")
        
        # Calculate and display some additional metrics
        utilization_rate = (result['actual_re_generated'] - result['surplus']) / result['actual_re_generated'] * 100
        total_capacity = (result['solar_capacity'] + result['wind_capacity'] + 
                         result['hydro_capacity'] + result['offshore_wind_capacity'])
        
        print(f"\nKey Performance Indicators:")
        print(f"System Utilization Rate: {utilization_rate:.1f}%")
        print(f"Total Installed Capacity: {total_capacity:,.2f} kW")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check the input parameters and try again.")

if __name__ == "__main__":
    main()
