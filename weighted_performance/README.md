# Weighted Performance (10-Minute Base)


---
## 📌 發電數據處理流程
1. **10 分鐘發電表現**（原始數據，儲存於 PostgreSQL）
2. **加權發電表現**（10 分鐘單位的加權平均）<--- **目前處理階段**
3. **TOU 加權發電表現**（依 TOU 時間段計算發電表現）

---
## 檔案說明
###  `power_plant_weighted_analysis.py`
- 從 PostgreSQL 擷取 **太陽能案場** 10 分鐘的歷史發電數據。
- 透過加權平均計算，得出 **太陽能** 每 10 分鐘的加權平均發電表現 (**SAP, Solar Average Performance**)。
- **數據單位**：原始數據為發電表現（%），SAP 也是以 % 表示。
- **加權平均計算方式**：
  
  \[ \frac{ \sum (案場 A 10min 發電表現 × 10min 發電量) + \sum (案場 B 10min 發電表現 × 10min 發電量) + ... }{ \sum (案場 A 10min 發電量) + \sum (案場 B 10min 發電量) + ... } \]

- **計算發電量公式**：
  \[ 案場 A 10min 發電量 (kWh) = 案場 A 10min 發電表現 (%) × \frac{1}{6} (hr) × 案場裝置容量 (kW) \]
- **選擇案場**：彰濱光、南鹽光
- **數據範圍**：2022、2023 年
- **輸出檔案**：`solar_average_performance.csv`

###  `wind_average_weighted_analysis.py`
- **發電技術**：陸域風力
- **選擇案場**：王功、台中港、觀園
- **數據範圍**：2022、2023 年
- **輸出檔案**：`wind_average_performance.csv`

###  `hydro_power_weighted_analysis.py`
- **發電技術**：小水力
- **選擇案場**：東部小水力
- **數據範圍**：2022、2023 年
- **輸出檔案**：`hydro_average_performance.csv`

###  `offshore_wind_weighted_analysis.py`
- **發電技術**：離岸風力
- **選擇案場**：離岸風力一期
- **數據範圍**：2022、2023 年
- **輸出檔案**：`offshore_wind_average_performance.csv`

