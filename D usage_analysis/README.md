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

| Cluster | peak_ratio  | nonsummer_midpeak_ratio | summer_midpeak_ratio | nonsummer_offpeak_ratio | summer_offpeak_ratio | nonsummer_sat_midpeak_ratio | summer_sat_midpeak_ratio | summer_to_nonsummer_ratio |
|---------|------------|------------------------|----------------------|------------------------|----------------------|--------------------------|--------------------------|--------------------------|
| 0       | 7.111746734  | 47.4120209  | 35.09968136  | 44.61459189  | 42.05960815  | 16.22639992  | 22.22450145  | 110.0057942  |
| 1       | 12.50916667  | 56.46008929  | 42.26554459  | 35.97762738  | 31.65065058  | 13.00613333  | 15.46510234  | 119.430625  |
| 2       | 8.987340514  | 50.77148322  | 37.94393088  | 41.15889498  | 38.98880716  | 14.3316383  | 18.51661647  | 120.9407782  |
| 3       | 8.163312198  | 46.37629831  | 33.59294612  | 45.06295229  | 42.7855234  | 17.66013527  | 24.65205738  | 132.4342542  |


📌 **用電分類類別如下**：  
- clustor 0: 24/7 year-round facility with stable seasonal demand
 
- cluster 1: office building/ commercial center

- clustor 2: two-shift factory or industrial facility with limited operating hours
 
- clustor 3: 24/7 factory with significant seasonal demand variation
