# Weighted Performance (10-Minute Base)


---
## 發電數據處理流程
1. **10 分鐘發電表現**（原始數據）--在postgreSQL裡
2. **加權發電表現**（10 分鐘單位的加權平均）<---NOW
3. **TOU 加權發電表現**（依 TOU 時間段計算發電表現）

---
## 檔案說明
###  `power_plant_weighted_analysis.py`
- 從 PostgreSQL 擷取 **太陽能案場** 10 分鐘的歷史發電數據。
- 透過加權平均計算，得出 **太陽能** 每 10 分鐘的加權平均發電表現 (**SAP, Solar Average Performance**)。
- **數據單位**：原始數據為發電表現（%），SAP 也是以 % 表示。
- #### 📌 加權平均計算方式

```
   Σ (P_A × E_A) + Σ (P_B × E_B) + ...
-------------------------------------------------
             Σ E_A + Σ E_B + ...
```

其中：
- P_A, P_B 分別為案場 A、B 在每 10 分鐘的發電表現（%）
- E_A, E_B 分別為案場 A、B 在每 10 分鐘的發電量（kWh）

#### 📌 計算發電量公式

```
E_A = P_A × (1/6) × C_A
```

其中：
- E_A 為案場 A 在 10 分鐘內的發電量（kWh）
- P_A 為案場 A 在 10 分鐘內的發電表現（%）
- C_A 為案場 A 的裝置容量（kW）
- 由於 1 小時內有 6 個 10 分鐘區間，因此發電時間為 1/6 小時

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



