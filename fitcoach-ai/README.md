# FitCoach AI — 智慧健身與熱量管理教練

FitCoach AI 是一個基於 Google Agent Development Kit (ADK) 與 Vertex AI Agent Platform 開發的對話式 AI 健身教練。協助使用者規劃個人化訓練、管理飲食熱量攝取，並結合結構化 A2UI 卡片、多模態影像與影音生成，提供全方位的健康追蹤體驗。

![FitCoach AI Demo](./demo.gif)

---

## 🌟 核心特色與架構能力 (Capabilities & Architecture)

本專案完全基於原始程式碼與 Google Cloud 託管服務實作，包含以下已接通的元件：

### 1. 🧠 跨對話長期記憶 (Vertex AI Memory Bank)
* **PreloadMemoryTool & 記憶回調**：接通 Vertex AI Memory Bank 服務（透過 `PreloadMemoryTool` 與 `generate_memories_callback` 中的 `add_session_to_memory`）。
* **客製化個人記憶**：自動記憶使用者的飲食偏好、過敏原禁忌（如堅果、海鮮、乳糖）、健身目標與身體特質，跨會話持續提供符合個人身體限制的專業建議。

### 2. 🗄️ 雲端結構化資料庫 (Google Cloud Firestore)
* **動作庫查詢 (`search_exercises`)**：自 Firestore 的 `exercises` 集合依部位（如 Legs, Chest, Cardio, Back）與關鍵字檢索動作指引、難度與燃燒熱量速率。
* **餐點庫查詢 (`search_food_catalog`)**：自 Firestore 的 `food_items` 集合查詢健康食材、烹調要點與三大營養素（蛋白質、碳水、脂肪）。
* **飲食記錄 (`log_food_entry`)**：記錄每日餐點內容、份量與卡路里。
* **運動記錄 (`log_workout_entry`)**：記錄重訓組數、重量、次數及估算之熱量消耗。
* **每日收支總覽 (`get_daily_summary`)**：即時聚合當日 Firestore 中所有飲食攝取與運動燃燒紀錄，計算當日淨卡路里。

### 3. 🎨 多模態影像與影音生成 (Google GenAI & Cloud Storage)
* **激勵獎章與視覺示意圖 (`generate_fitness_image`)**：
  * 調用 **Google Imagen** (`gemini-3.1-flash-lite-image`) 模型。
  * 自動將圖片作為 Session Artifact 保存（`tool_context.save_artifact`），並上傳至公開 Google Cloud Storage Bucket，回傳公開網址於介面展示。
* **動作示範短影音 (`generate_fitness_video`)**：
  * 調用 **Google Omni 模型** (`gemini-omni-flash-preview` 全球區域)。
  * 生成高品質健身動作教學動態短影片，存入 Session Artifacts 並上傳至 Cloud Storage。

### 4. 🧮 雲端程式碼沙盒計算與圖表生成 (Agent Engine Code Sandbox)
* **TDEE 與營養素試算 (`calculate_tdee_and_macro_targets`)**：在受隔離的 Agent Engine Python Sandbox 環境中執行 Mifflin-St Jeor 公式精確試算代謝率。
* **進度趨勢圖表 (`generate_progress_chart`)**：沙盒執行 matplotlib 動態繪製熱量平衡與體重趨勢圖，並上傳至 Cloud Storage 公開展示。

### 5. 🌐 外部食譜即時檢索 (`search_online_recipes`)
* 調用 TheMealDB 公開 API，全球即時檢索健康增肌減脂食譜與烹飪指引。

### 6. 🖼️ A2UI 結構化介面規範 (v0.8 Basic Catalog)
* 透過 `after_model_callback` (a2ui_callback) 將 Agent 回應包裝為 A2UI 規範訊息。
* 前端原生輕量渲染器支援 `Card`, `Column`, `Row`, `Text`, `Divider`, `Image`, `Video`, `Icon` 等組件，對話氣泡內建 HTML5 影片播放器與圖文卡片。

---

## 📋 功能實作對照表 (Implementation Status)

| 功能項目 | 狀態 | 支援技術 / 服務 |
| :--- | :---: | :--- |
| 跨會話偏好與過敏原記憶 | ✅ 已實作 | Vertex AI Memory Bank (`PreloadMemoryTool`) |
| 訓練動作庫與飲食資料查詢 | ✅ 已實作 | Google Cloud Firestore (`exercises`, `food_items`) |
| 運動與飲食數據紀錄 | ✅ 已實作 | Google Cloud Firestore (`workout_logs`, `food_logs`) |
| 每日熱量與巨量營養素統計 | ✅ 已實作 | Google Cloud Firestore 聚合計算 |
| TDEE / 巨量營養素沙盒計算 | ✅ 已實作 | Agent Engine Sandbox Code Executor (Python) |
| 視覺化趨勢圖動態生成 | ✅ 已實作 | Sandbox Matplotlib + Cloud Storage |
| 成就徽章與餐點圖片生成 | ✅ 已實作 | Google Imagen + Cloud Storage |
| 動作示範動態短影片生成 | ✅ 已實作 | Google Omni (`gemini-omni-flash-preview`) + Cloud Storage |
| 全球線上食譜搜尋 | ✅ 已實作 | TheMealDB REST API |
| 結構化圖文與影音卡片呈現 | ✅ 已實作 | A2UI v0.8 規範 + 前端自訂渲染器 |
| 行動裝置相機即時相片即時分析 | 📝 規劃中，尚未實作 | 預計整合前端攝影機串流與 Gemini 多模態視覺輸入 |

---

## 🛠️ 本地開發與啟動指南 (Setup & Run Instructions)

### 環境需求
* Python 3.11 或 3.12
* Google Cloud CLI (`gcloud`) 與 `agents-cli` (v1.4+)
* 已完成 Google Cloud 專案設定與 Application Default Credentials (ADC) 驗證

### 1. 取得專案並安裝相依套件

```bash
git clone <your-repo-url>
cd fitcoach-ai

# 安裝後端 Agent 依賴
uv sync
```

### 2. 本地啟動前端介面 (Local Web UI)

前端為獨立的 FastAPI 服務，透過 A2A 協定代理與 Agent Platform 溝通：

```bash
cd frontend

# 安裝前端依賴
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 設定環境變數 (填入對應的 Agent 資源路徑與目錄)
export AGENT_ENGINE_RESOURCE_NAME="<your-agent-engine-resource-name>"
export AGENT_DIRECTORY="app"
export PORT="8080"

# 啟動前端伺服器
python3 main.py
```

伺服器啟動後，使用瀏覽器開啟本機對應的通訊埠即可進入 FitCoach AI 互動對話畫面。

### 3. Agent 部署指令 (Agent Platform Deployment)

若需將 Agent 重新部署至 Vertex AI Agent Platform：

```bash
uv run agents-cli deploy --no-confirm-project --update-env-vars MEALDB_API_KEY=1
```
