# MogooMVP

## 專案簡介

MogooMVP 是一個以 Python 為核心的專案，目標是建立一個 B2B 再生能源數據庫，讓企業、媒體、政府與產業組織能夠更輕鬆地取得相關資訊。

## 主要 Python 檔案說明

- **time_of_use_visualization.py**：
  - 根據台電三段式時間電價劃分的不同電力歸屬時間段 (peak, mid-peak, off-peak)。
  - 將一個禮拜的 24 小時時間段定義電力時間區間並進行視覺化。
  - (請參考 `summer_tou.png` & `nonsummer_tou.png`)

- **power_plant_analysis.py / power_plant_performance_analysis.py / power_plant_comparison.py**：
  - 確認每個案場的資料完整度。
  - 確保發電表現、趨勢沒有極端值出現。
  - 測試同一種發電技術的不同案場間的發電表現相關性。

- **power_plant_weights.py / wind_farm_weighted_analysis.py**：
  - 透過不同案場（同技術能源）的歷史數據進行分析。
  - 不同的發電技術類型各會有一個加權平均發電表現。
  - 太陽能的加權平均發電表現 (SAP, Solar Average Performance) 由 2022 年與 2023 年的南鹽光、彰濱光兩案場發電表現加權計算。
  - 陸域風力的加權平均發電表現 (WAP, Wind Average Performance) 由 2022、2023 年的台中港、王功、觀園歷史發電數據加權平均計算。
  - (請參考 `solar_average_performance.csv` & `wind_average_performance.csv`)

