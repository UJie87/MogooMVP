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
- 總共有跑了三種，K=2; K=3; K=4，計算結果, PCA, and distribution 可以在  `power_usage_plot` 檔案夾裡面看到
- 最後決定K=3，其結果如下

| cluster | peak_ratio | midpeak_ratio | offpeak_ratio | sat_midpeak_ratio |
|---------|------------|---------------|---------------|-------------------|
| 0 | 1.48 | 49.48 | 42.02 | 14.67 |
| 1 | 19.04 | 30.79 | 42.47 | 25.61 |
| 2 | 49.00 | 17.92 | 26.11 | 4.40 |

📌 **用電分類類別如下**：  
- clustor 0: 日間辦公室&小型工廠
  - 特徵: 白天用電量較高(midpeak ratio高)，晚上與周末低耗能
  - 對應場所: 辦公大樓、商業機構(銀行、學校)、小型製造業(食品加工、小型電子組裝)

- clustor 1: 24/7工廠(夜間減產，無24hr運轉的大型機組)
  - 特徵: 全天運行但夜間減產(peak ratio不高)，夜間用電下降
  - 對應場所: 一般24hr工廠(塑膠加工、一般電子廠、紡織廠)、冷鏈倉儲(夜間仍須部分冷氣運作)、物流中心(倉儲設備持續運作，但夜間人力少)
 
- clustor 2: 24/7 高耗能工廠(機組全年無休)
  - 特徵: 尖峰時段耗能及高，夜間仍舊維持高能耗
  - 對應場所: 鋼鐵廠與煉鋁廠(高爐、電弧爐無法關閉)、半導體晶圓廠(機台與無塵室全年運作)、石化廠與造紙廠(持續運轉的大型機組)、大型冷鏈倉儲(全天候溫控，幾乎無法關閉設備)
