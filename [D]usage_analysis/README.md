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
- 總共有跑了三種，K=2; K=3; k=4，計算結果, PCA, and distribution 可以在  `power_usage_plot` 檔案夾裡面看到
- 最後決定K=4，其結果如下 (詳細的數據請看 `kmeans_analysis_k4`)

| cluster | peak_ratio | midpeak_ratio (summer) | offpeak_ratio (summer) | sat_midpeak_ratio (summer) | midpeak_ratio (nonsummer) | offpeak_ratio (nonsummer) | sat_midpeak_ratio (nonsummer) |
|---------|------------|------------------------|------------------------|----------------------------|---------------------------|---------------------------|-------------------------------|
| 0 | 7.309 | 35.301 | 41.776 | 21.838 | 47.627 | 44.363 | 16.030 |
| 1 | 12.509 | 42.265 | 31.650 | 15.465 | 56.460 | 435.977 | 13.006 |
| 2 | 8.987 | 37.943 | 38.988 | 18.516 | 50.771 | 41.158 | 14.331 |
| 3 | 7.678 | 33.742 | 42.922 | 24.479 | 46.393 | 45.233 | 17.522 |

📌 **用電分類類別如下**：  
- clustor 0: 混合型
  - 特徵: 主要用電量集中在白天，夜間與周末用電顯著下降。夏季mid-peak用電比例高，雖然off-peak 還是有一定占比，可能是因為設備待機或是受大樓公共設施影響
  - 對應場所: 辦公大樓、商業機構(銀行、學校)
 
- cluster 1: 日間辦公室

- clustor 2: 24/7工廠(夜間減產，無24hr運轉的大型機組)
  - 特徵: 全天運行但夜間減產(peak ratio不高)，夜間用電下降
  - 對應場所: 一般24hr工廠(塑膠加工、一般電子廠、紡織廠)、冷鏈倉儲(夜間仍須部分冷氣運作)、物流中心(倉儲設備持續運作，但夜間人力少)
 
- clustor 3: 24/7 高耗能工廠(機組全年無休)
  - 特徵: 尖峰時段耗能及高，夜間仍舊維持高能耗
  - 對應場所: 鋼鐵廠與煉鋁廠(高爐、電弧爐無法關閉)、半導體晶圓廠(機台與無塵室全年運作)、石化廠與造紙廠(持續運轉的大型機組)、大型冷鏈倉儲(全天候溫控，幾乎無法關閉設備)
