# My agent: FitCoach AI (健身與熱量管理教練)
One-liner: 一個對話式 AI 教練，協助使用者制定個人化健身計畫、記錄訓練與飲食熱量，並透過視覺化卡片追蹤健身進度。

Tool coverage:
- Memory: 記住使用者的身體數據（身高、體重、目標）、每日熱量目標 (TDEE)、飲食偏好與過敏原、歷史訓練強度。
- Tools: 
  - log_workout: 記錄運動項目、組數、重量、燃燒熱量。
  - log_food: 記錄飲食餐點、卡路里與三大營養素。
  - get_daily_summary: 計算並查詢當日熱量收支與營養素統計。
- Catalog/UI: 健身訓練動作庫卡片、客製化食譜建議卡片、A2UI 進度摘要卡片。
- Image gen: 產生餐點呈現示意圖、運動姿勢指南圖或里程碑激勵獎章圖。
- Sandbox: 計算 TDEE/BMR、評估熱量赤字/盈餘曲線、計算運動量負荷進展。

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code execution for precise calorie/nutrition math and progress charting.
