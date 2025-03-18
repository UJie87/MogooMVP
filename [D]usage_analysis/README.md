# Various Electricity Usage Analaysis and Categorize

整理了31個案場2022-2024年每月不同時間段的用電數據，透過kmeans方式歸納整理，歸納出三種用電場所型態。

---

## 用電數據處理流程
1. **每月帳單資訊**（原始數據）--在postgreSQL裡
2. **各案場的彙整資訊**-- 跟原始數據是一樣的，只有把更改表格格式(透過create_summary.py)
3. **歸納出不同用電場所形態**-- 透過上面的數據，透過k-means的方式歸納出三種用電型態

---

## 檔案說明
###  `create_summary.py`, `interactive_plot_power_usage.py`, `update_all_analysis.py`
**功能**：  
- 先由 `create_summary.py`將原始資料整理成以案場為單位的SQL table， table欄位:
  - year, month
  - time_period: peak, mid-peak, Sat. mid-peak, off-peak
  - total usage: 總用電量(kWh)
- 再透過 `interactive_plot_power_usage.py`做成不同TOU下的各案場使用量互動圖表
  - 輸出 `interactive_%.html`
- `update_all_analysis.py`: 只是前面兩個東西輸出之後發現有異常值，因此回去修正原始資料庫，用這個檔案就可以全部同步更新出上面的產物。

---

###  `power_kmeans_analysis.py`
- 獲得不同案場的歷年逐月用電資訊後，透過K means 方法將案場的用電型態歸類
- K means factor
  - peak ratio= peak usage/ total usage
  - mid-peak ratio = mid-peak usage/ total usage
  - off-peak ratio= off-peak usage/ total usage
  - Sat. mid-peak ratio= Sat. mid-peak/ mid-peak
- 總共有跑了三種，K=2; K=3; K=4，計算結果, PCA, and distribution 可以在 power_usage_plot檔案夾裡面看到
- 最後決定K=3，其結果如下

| 星期 | 時間區段 | 類別 |
|------|----------|---------|
| 平日 | 16:00 - 21:59 | **Peak** |
| 平日 | 9:00 - 15:59 | **Mid-peak** |
| 平日 | 22:00 - 23:59 | **Mid-peak** |
| 平日 | 00:00 - 8:59 | **Off-peak** |

📌 **計算方式**（示例）：  
假設 `2025年1月 Sat. mid-peak` 時段內：
- **SAP = 13.55%**，表示 **太陽能裝置容量的平均發電表現為 13.55%**
- 若該案場的裝置容量為 `100 kW`，則：
  - 有效發電容量 = `100 kW × 13.55% = 13.55 kW`
  - `Sat. mid-peak` 時段在 1 月內共計 **60 小時**
  - 該時段的發電量 = `100 kW × 13.55% × 60 hr = 813 kWh`

---

## ⏳ 三段式時間電價 (TOU) 定義
### 🔹 夏季 (5/16 - 10/15)
| 星期 | 時間區段 | 類別 |
|------|----------|---------|
| 平日 | 16:00 - 21:59 | **Peak** |
| 平日 | 9:00 - 15:59 | **Mid-peak** |
| 平日 | 22:00 - 23:59 | **Mid-peak** |
| 平日 | 00:00 - 8:59 | **Off-peak** |
| 星期六 | 9:00 - 23:59 | **Sat. Mid-peak** |
| 星期六 | 00:00 - 08:59 | **Off-peak** |
| 星期日 | 00:00 - 23:59 | **Off-peak** |

### 🔹 非夏季 (10/16 - 5/15)
| 星期 | 時間區段 | 類別 |
|------|----------|---------|
| 平日 | 6:00 - 10:59 | **Mid-peak** |
| 平日 | 14:00 - 23:59 | **Mid-peak** |
| 平日 | 00:00 - 5:59 | **Off-peak** |
| 平日 | 11:00 - 13:59 | **Off-peak** |
| 星期六 | 6:00 - 10:59 | **Sat. Mid-peak** |
| 星期六 | 14:00 - 23:59 | **Sat. Mid-peak** |
| 星期六 | 00:00 - 5:59 | **Off-peak** |
| 星期六 | 11:00 - 13:59 | **Off-peak** |
| 星期日 | 00:00 - 23:59 | **Off-peak** |
