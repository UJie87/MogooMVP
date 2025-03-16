# MogooMVP

MVP目標:將發電資訊與用電資訊進行匹配(matching)並提供出不同scenario的procurement portfolio

## 發電數據處理流程[G]
*每一個步驟都有一個自己的資料夾*
1. **10 分鐘發電表現**（原始數據）--在postgreSQL裡
2. **加權發電表現**（10 分鐘單位的加權平均）
3. **TOU 加權發電表現**（依 TOU 時間段計算發電表現）

## 需電數據處理流程[D]
1. **買家歷史購電量**(原始數據) --在postgreSQL裡
2. **將購電量依不同型態的用電場所歸納出用電pattern**(TOU時間的用電，日班工廠、24hr工廠、辦公大樓)

## 匹配[M]
1. 使用者輸入年用電量、用電場所類型-- 帶入[D]usage_pattern 得出以TOU為單位的用電曲線
2. 使用者輸入再生能源目標達成年份、再生能源目標、未來用電計畫-- 得出特定時間點(目標年)的再生能源需求量
3. 以tou為單位，進行再生能源需求量與不同再生能源技術發電量的匹配。匹配考量因數的優先順序依scenario 決定
4. 匹配的限制: 推薦出的採購組合裝置容量量體不可以大於再生能源目標達成年份該年預估的再生能源技術類型裝置容量

## Scenario
### minimized cost scenario
### minimized surplus power scenario
### comprehensive solution scenario (目前先不用)

## 一些備註
結果先給最終的recommended portfolio就好，先不考慮歷年的採購推薦!
