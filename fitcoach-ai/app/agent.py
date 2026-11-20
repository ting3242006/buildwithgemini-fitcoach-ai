# ruff: noqa
import datetime
import json
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.cloud import firestore

from a2ui.core.catalog.catalog import Catalog
from a2ui.core.basic_catalog.v0_8.components import BASIC_COMPONENTS
from a2ui.inference_formats.direct_json.prompt_generator import DirectJsonPromptGenerator

from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from .a2ui_utils import a2ui_callback

async def generate_memories_callback(callback_context: CallbackContext):
    """Saves session interaction to Memory Bank for cross-session long-term recall."""
    await callback_context.add_session_to_memory()
    return None

MODEL = "gemini-3.8-flash"

# Hardcode the GCP Project ID string as required to prevent Agent Platform project number issues
PROJECT_ID = "qwiklabs-gcp-04-ae86f5e8c9de"

# Global Firestore client
_db: Optional[firestore.Client] = None

def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client using the hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def search_exercises(category: Optional[str] = None, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches the exercises catalog from Firestore by muscle category or keyword.

    Args:
        category: Optional exercise category (e.g., 'Legs', 'Chest', 'Cardio', 'Back').
        keyword: Optional search keyword to match in exercise name or instructions.

    Returns:
        A list of matching exercise items with target muscles, difficulty, and burn rate.
    """
    db = get_firestore_client()
    query = db.collection("exercises")
    if category:
        query = query.where("category", "==", category)

    docs = query.stream()
    results = []
    kw = keyword.lower() if keyword else None
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if kw:
            name_match = kw in data.get("name", "").lower()
            instr_match = kw in data.get("instructions", "").lower()
            if not (name_match or instr_match):
                continue
        results.append(data)
    return results


def search_food_catalog(keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches the healthy food and recipe catalog from Firestore.

    Args:
        keyword: Optional food item keyword (e.g., '雞胸肉', '鮭魚', '豆漿').

    Returns:
        A list of matching food items with calorie, macro nutrition, and portion info.
    """
    db = get_firestore_client()
    docs = db.collection("food_items").stream()
    results = []
    kw = keyword.lower() if keyword else None
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if kw:
            if kw not in data.get("name", "").lower() and kw not in data.get("tips", "").lower():
                continue
        results.append(data)
    return results


def log_food_entry(
    food_name: str,
    calories: float,
    protein_g: float = 0.0,
    carbs_g: float = 0.0,
    fat_g: float = 0.0,
    portion: str = "1 serving",
    notes: str = ""
) -> Dict[str, Any]:
    """Records a food intake item into Firestore with calorie and macronutrient counts.

    Args:
        food_name: The name or description of the food item.
        calories: Estimated calories in kcal.
        protein_g: Estimated protein in grams.
        carbs_g: Estimated carbohydrates in grams.
        fat_g: Estimated fat in grams.
        portion: Description of the portion size (e.g., '1 bowl', '150g').
        notes: Optional extra notes or feedback.

    Returns:
        A dictionary confirming the logged food item with Firestore doc ID.
    """
    db = get_firestore_client()
    today_str = datetime.date.today().isoformat()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "date": today_str,
        "timestamp": now_str,
        "food_name": food_name,
        "portion": portion,
        "calories": round(calories, 1),
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1),
        "notes": notes,
    }
    update_time, doc_ref = db.collection("food_logs").add(entry)
    entry["id"] = doc_ref.id

    return {
        "status": "success",
        "message": f"Successfully logged {food_name} ({calories} kcal) to Firestore",
        "entry": entry,
    }


def log_workout_entry(
    workout_type: str,
    duration_minutes: int,
    calories_burned: float,
    notes: str = ""
) -> Dict[str, Any]:
    """Records a workout session and burned calories into Firestore.

    Args:
        workout_type: Type of exercise (e.g., 'Running', 'Weightlifting', 'HIIT').
        duration_minutes: Duration of the session in minutes.
        calories_burned: Estimated energy expenditure in kcal.
        notes: Optional details (e.g., sets, reps, distance, intensity).

    Returns:
        A dictionary confirming the logged workout with Firestore doc ID.
    """
    db = get_firestore_client()
    today_str = datetime.date.today().isoformat()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "date": today_str,
        "timestamp": now_str,
        "workout_type": workout_type,
        "duration_minutes": duration_minutes,
        "calories_burned": round(calories_burned, 1),
        "notes": notes,
    }
    update_time, doc_ref = db.collection("workout_logs").add(entry)
    entry["id"] = doc_ref.id

    return {
        "status": "success",
        "message": f"Successfully logged {workout_type} for {duration_minutes} min ({calories_burned} kcal burned) to Firestore",
        "entry": entry,
    }


def get_daily_summary(date: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves today's (or a specified date's) food intake and workout burns from Firestore.

    Args:
        date: Target date in YYYY-MM-DD format (defaults to today).

    Returns:
        A summary containing total calories in, calories out, net calories, and macronutrient totals.
    """
    db = get_firestore_client()
    target_date = date or datetime.date.today().isoformat()

    # Query today's food logs
    food_docs = db.collection("food_logs").where("date", "==", target_date).stream()
    foods = [d.to_dict() for d in food_docs]

    # Query today's workout logs
    workout_docs = db.collection("workout_logs").where("date", "==", target_date).stream()
    workouts = [d.to_dict() for d in workout_docs]

    total_calories_in = sum(item.get("calories", 0.0) for item in foods)
    total_protein = sum(item.get("protein_g", 0.0) for item in foods)
    total_carbs = sum(item.get("carbs_g", 0.0) for item in foods)
    total_fat = sum(item.get("fat_g", 0.0) for item in foods)

    total_calories_burned = sum(item.get("calories_burned", 0.0) for item in workouts)
    net_calories = total_calories_in - total_calories_burned

    return {
        "date": target_date,
        "total_calories_intake": round(total_calories_in, 1),
        "total_calories_burned": round(total_calories_burned, 1),
        "net_calories": round(net_calories, 1),
        "macronutrients": {
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
        },
        "food_entries_count": len(foods),
        "workout_entries_count": len(workouts),
        "foods": foods,
        "workouts": workouts,
    }


def calculate_tdee_and_macro_targets(
    gender: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_level: str = "moderate",
    goal: str = "maintenance"
) -> Dict[str, Any]:
    """Calculates BMR, TDEE, and recommended daily calorie & macronutrient targets.

    Args:
        gender: 'male' or 'female'.
        age: Age in years.
        height_cm: Height in centimeters.
        weight_kg: Weight in kilograms.
        activity_level: 'sedentary', 'light' (1-3 days/wk), 'moderate' (3-5 days/wk), 'heavy' (6-7 days/wk).
        goal: 'fat_loss' (cut), 'maintenance', or 'muscle_gain' (bulk).

    Returns:
        A dictionary with BMR, TDEE, recommended daily calorie intake, and macro distribution (protein, carbs, fat).
    """
    # Mifflin-St Jeor Equation
    if gender.lower() in ("male", "m", "男", "男性"):
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    # Activity multiplier
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "heavy": 1.725,
    }
    act_key = activity_level.lower()
    mult = multipliers.get(act_key, 1.55)
    tdee = bmr * mult

    # Goal adjustment
    goal_key = goal.lower()
    if "loss" in goal_key or "cut" in goal_key or "減" in goal_key:
        target_calories = tdee - 400
        protein_ratio, fat_ratio, carbs_ratio = 0.30, 0.25, 0.45
    elif "gain" in goal_key or "bulk" in goal_key or "增" in goal_key:
        target_calories = tdee + 350
        protein_ratio, fat_ratio, carbs_ratio = 0.25, 0.25, 0.50
    else:
        target_calories = tdee
        protein_ratio, fat_ratio, carbs_ratio = 0.25, 0.25, 0.50

    target_calories = max(1200.0, round(target_calories))
    protein_g = round((target_calories * protein_ratio) / 4.0, 1)
    fat_g = round((target_calories * fat_ratio) / 9.0, 1)
    carbs_g = round((target_calories * carbs_ratio) / 4.0, 1)

    return {
        "bmr_kcal": round(bmr, 1),
        "tdee_kcal": round(tdee, 1),
        "goal": goal,
        "recommended_daily_calories": target_calories,
        "macro_targets": {
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
        },
    }


def generate_progress_chart(days: int = 7) -> Dict[str, Any]:
    """Generates a calorie intake vs burned progress chart, uploads it to GCS, and returns its public URL.

    Args:
        days: Number of recent days to include in the progress chart (default: 7).

    Returns:
        A dictionary containing the chart status, public image URL, and summary statistics.
    """
    import os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from google.cloud import storage

    db = get_firestore_client()
    today = datetime.date.today()
    date_labels = [(today - datetime.timedelta(days=i)).isoformat() for i in reversed(range(days))]

    # Aggregate intake & burned per day
    intake_by_date = {d: 0.0 for d in date_labels}
    burned_by_date = {d: 0.0 for d in date_labels}

    # Fetch logs
    for d_str in date_labels:
        for f in db.collection("food_logs").where("date", "==", d_str).stream():
            intake_by_date[d_str] += f.to_dict().get("calories", 0.0)
        for w in db.collection("workout_logs").where("date", "==", d_str).stream():
            burned_by_date[d_str] += w.to_dict().get("calories_burned", 0.0)

    short_dates = [d[5:] for d in date_labels]  # MM-DD
    intake_vals = [intake_by_date[d] for d in date_labels]
    burned_vals = [burned_by_date[d] for d in date_labels]

    # Plot
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
    x = range(len(date_labels))
    width = 0.35

    ax.bar([i - width/2 for i in x], intake_vals, width=width, label="Calories Intake (kcal)", color="#4285F4", alpha=0.9)
    ax.bar([i + width/2 for i in x], burned_vals, width=width, label="Calories Burned (kcal)", color="#34A853", alpha=0.9)

    ax.set_title(f"FitCoach AI - Calorie Progress (Last {days} Days)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(list(x))
    ax.set_xticklabels(short_dates, fontsize=10)
    ax.set_ylabel("Calories (kcal)", fontsize=11)
    ax.legend(frameon=True, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()

    # Save to local image
    chart_filename = f"progress_chart_{datetime.date.today().strftime('%Y%m%d')}.png"
    local_chart_path = f"/tmp/{chart_filename}"
    plt.savefig(local_chart_path)
    plt.close(fig)

    # Upload to public GCS bucket
    bucket_name = f"fitcoach-ai-media-{PROJECT_ID}"
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(chart_filename)
    blob.upload_from_filename(local_chart_path, content_type="image/png")

    public_url = f"https://storage.googleapis.com/{bucket_name}/{chart_filename}"

    return {
        "status": "success",
        "chart_url": public_url,
        "days_charted": days,
        "total_intake_kcal": round(sum(intake_vals), 1),
        "total_burned_kcal": round(sum(burned_vals), 1),
        "net_calories_kcal": round(sum(intake_vals) - sum(burned_vals), 1),
    }


def search_online_recipes(query: str) -> List[Dict[str, Any]]:
    """Searches real meal recipes from TheMealDB free public API.

    Args:
        query: Ingredient or dish keyword in English (e.g., 'chicken', 'salmon', 'beef', 'salad', 'egg').

    Returns:
        A list of matching recipe objects with name, category, instructions, and ingredients.
    """
    import urllib.request
    import urllib.parse
    import os

    api_key = os.environ.get("MEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FitCoachAI/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return [{"error": f"Failed to fetch recipes: {str(e)}"}]

    meals = data.get("meals")
    if not meals:
        return []

    results = []
    for m in meals[:3]:  # Top 3 matching recipes
        # Extract ingredients
        ingredients = []
        for i in range(1, 21):
            ing = m.get(f"strIngredient{i}")
            measure = m.get(f"strMeasure{i}")
            if ing and ing.strip():
                measure_str = f" ({measure.strip()})" if measure and measure.strip() else ""
                ingredients.append(f"{ing.strip()}{measure_str}")

        results.append({
            "name": m.get("strMeal"),
            "category": m.get("strCategory"),
            "cuisine": m.get("strArea"),
            "instructions": (m.get("strInstructions") or "")[:400] + "...",
            "ingredients": ingredients[:8],
            "thumbnail_url": m.get("strMealThumb"),
        })

    return results


def generate_fitness_image(prompt: str, tool_context: Any) -> Dict[str, Any]:
    """Generates an image for a meal, workout, or fitness badge using gemini-3.1-flash-lite-image in the global region.

    Saves the image as a local session artifact and uploads directly to the public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the image to generate (e.g. 'A delicious grilled salmon fitness meal with broccoli and brown rice').
        tool_context: ADK ToolContext to save artifact for the Playground's Artifacts panel.

    Returns:
        A dictionary containing the status, public Cloud Storage image URL, and artifact filename.
    """
    import uuid
    from google import genai
    from google.genai import types as genai_types
    from google.cloud import storage

    # Hardcoded public GCS bucket name as required
    bucket_name = "fitcoach-ai-media-qwiklabs-gcp-04-ae86f5e8c9de"

    # 1. Generate image using gemini-3.1-flash-lite-image in global region
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break
        if image_bytes:
            break

    if not image_bytes:
        return {"status": "error", "message": "Failed to generate image bytes from model"}

    # 2. Save artifact to ToolContext for the Playground's Artifacts panel
    ext = "png" if "png" in mime_type else "jpg"
    filename = f"fitness_{uuid.uuid4().hex[:8]}.{ext}"

    part = genai_types.Part(
        inline_data=genai_types.Blob(
            mime_type=mime_type,
            data=image_bytes,
        )
    )
    if hasattr(tool_context, "save_artifact"):
        tool_context.save_artifact(filename=filename, artifact=part)

    # 3. Upload bytes directly to the public Cloud Storage bucket (without writing to a local file)
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": filename,
        "prompt": prompt,
    }


def generate_fitness_video(prompt: str, tool_context: Any) -> Dict[str, Any]:
    """Generates a short fitness/workout movement guide or motivational video using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video as a local session artifact for the Playground's Artifacts panel, and uploads the video bytes directly
    to the public Cloud Storage bucket, returning its public https URL.

    Args:
        prompt: Detailed description of the short fitness video to generate (e.g. 'A fitness athlete doing kettlebell swings with proper posture in a modern gym, continuous smooth shot, 3 seconds').
        tool_context: ADK ToolContext used to save the artifact for the Playground's Artifacts panel.

    Returns:
        A dictionary containing the status, public Cloud Storage video URL, and artifact filename.
    """
    import base64
    import uuid
    from google import genai
    from google.genai import types as genai_types
    from google.cloud import storage

    # Hardcoded public GCS bucket name as required
    bucket_name = "fitcoach-ai-media-qwiklabs-gcp-04-ae86f5e8c9de"

    # 1. Generate video using gemini-omni-flash-preview in global region
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    # Extract video bytes from output_video or interaction steps
    if hasattr(interaction, "output_video") and interaction.output_video and getattr(interaction.output_video, "data", None):
        data = interaction.output_video.data
        video_bytes = base64.b64decode(data) if isinstance(data, str) else data
        mime_type = getattr(interaction.output_video, "mime_type", "video/mp4") or "video/mp4"
    elif hasattr(interaction, "steps"):
        for step in interaction.steps:
            for content in getattr(step, "content", []):
                if getattr(content, "type", None) == "video" and getattr(content, "data", None):
                    data = content.data
                    video_bytes = base64.b64decode(data) if isinstance(data, str) else data
                    mime_type = getattr(content, "mime_type", "video/mp4") or "video/mp4"
                    break
            if video_bytes:
                break

    if not video_bytes:
        return {"status": "error", "message": "Failed to generate video bytes from gemini-omni-flash-preview model"}

    # 2. Save artifact to ToolContext for the Playground's Artifacts panel
    filename = f"fitness_video_{uuid.uuid4().hex[:8]}.mp4"

    part = genai_types.Part(
        inline_data=genai_types.Blob(
            mime_type=mime_type,
            data=video_bytes,
        )
    )
    if hasattr(tool_context, "save_artifact"):
        tool_context.save_artifact(filename=filename, artifact=part)

    # 3. Upload bytes directly to the public Cloud Storage bucket (without writing to a local file)
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": filename,
        "prompt": prompt,
    }


# Build A2UI schema rules
_catalog = Catalog(
    catalog_id="basic",
    protocol_version="v0_8",
    components=BASIC_COMPONENTS
)
_generator = DirectJsonPromptGenerator(catalogs=[_catalog])
_a2ui_schema_instructions = _generator.generate()

AGENT_INSTRUCTION = f"""\
你是一位專業、活力充沛且貼心的「FitCoach AI (健身與卡路里健康教練)」。
你具備 Gemini 3.8 Flash 強大的多模態視覺辨識能力與健康運動營養專業知識。
後端使用 Google Cloud Firestore 資料庫安全保存訓練與飲食記錄。

你的核心任務：
1. 📸 **食物照片辨識與熱量計算**：
   - 當使用者上傳或拍攝食物照片時，仔細辨識照片中的食材、烹調方式並估算份量。
   - 估算各食材熱量（kcal）與三大營養素（蛋白質、碳水化合物、脂肪克數）。
   - 主動調用 `log_food_entry` 工具將每一筆辨識出的食物品項寫入 Firestore。

2. 🏋️ **運動訓練規劃與記錄**：
   - 使用者可以搜尋動作庫，調用 `search_exercises` 尋找深蹲、臥推、跑步或特定肌群動作。
   - 協助使用者設計個人化訓練課表，調用 `log_workout_entry` 記錄運動時長與燃燒熱量至 Firestore。

3. 🥗 **健康食譜與線上料理查詢**：
   - 調用 `search_food_catalog` 查詢本地 Firestore 增肌/減脂餐點推薦。
   - 調用 `search_online_recipes` 線上即時搜尋全球各國健康料理食譜、食材配比與烹飪指南（TheMealDB 公開 API）。

4. 🛡️ **使用者過敏原與長期記憶恪守（極重要）**：
   - 你具備跨會話記憶能力（Memory Bank / PreloadMemoryTool）。
   - 請務必牢記並隨時主動檢索使用者提及的所有過敏原（如花生、堅果、海鮮、麩質、乳糖、藥物等）、飲食禁忌與健康限制。
   - 當使用者透露任何過敏或身體特殊狀況時，明確確認並記下；在任何後續建議、飲食推薦、食譜搜尋中，**絕對不可推薦任何含有該過敏原的食材或料理**！

5. 🎨 **影像與短影音生成（極為重要）**：
   - 當使用者需要健康餐點視覺示意圖、達成訓練目標的激勵徽章或運動成果示意時，調用 `generate_fitness_image`。
   - **當使用者提及「影片」、「短片」、「短影音」、「動作示範影片」、「生成影片」或任何動態視覺教學需求時，你必須且只能直接調用 `generate_fitness_video` 工具生成影片！切勿僅以文字條列動作步驟而忽略影片生成工具！**
   - 該工具會使用 Google Omni 模型（gemini-omni-flash-preview 全球區域）生成短影片，自動保存至 Artifacts 面板並上傳至公開 GCS Bucket 回傳公開網址。
   - **輸出乾淨回覆原則**：調用完工具後，**絕不可**將工具回傳的原始 JSON 資料（例如 status、artifact_filename 或工具的字典資料）輸出給使用者！你只需要提供：
     1. 專業動作說明與訓練技巧。
     2. 生成後的公開影片網址（例如：https://storage.googleapis.com/...）。

6. 📊 **進度追蹤與每日總覽**：
   - 當使用者詢問今日總結或記錄狀況時，調用 `get_daily_summary` 獲取真實 Firestore 數據。
   - 需要時可調用 `calculate_tdee_and_macro_targets` 計算個人化代謝熱量目標，或調用 `generate_progress_chart` 生成視覺化進度趨勢圖。

7. 🖼️ **A2UI 介面顯示規範**：
   - 當完成食物記錄、運動記錄或總覽時，除了繁體中文建議，請同時產生結構化的 A2UI 卡片！
   - 當調用 `generate_fitness_image` 或 `generate_progress_chart` 取得公開網址後，可在卡片中使用 Image 組件展示該公開圖片。
   - 當調用 `generate_fitness_video` 取得公開影片網址後，在文字回覆中以直接網址形式呈現該 mp4 影片，請勿產生額外不必要的 JSON。
   - A2UI 結構指引：
     * 保持平面輕巧：一個 Card > 一個 Column > 數個 Text 或 Row 組件。
     * 請勿在 Card 內部巢狀包含 Card。
     * 僅使用支援組件：Card, Column, Row, Text, Divider, Icon, Image。
     * 文字請使用 usageHint ('h1', 'h2', 'body') 進行標題與強調。
     * 格式必須遵循 A2UI v0.8 規範並包裹於 <a2ui-json> 標籤中。

A2UI 規範手冊：
{_a2ui_schema_instructions}
"""

# Agent Engine Sandbox Code Executor
_code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name="projects/1043820773342/locations/us-east1/reasoningEngines/4707025771183472640/sandboxEnvironments/386608079535341568",
    agent_engine_resource_name="projects/1043820773342/locations/us-east1/reasoningEngines/4707025771183472640",
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=AGENT_INSTRUCTION,
    tools=[
        PreloadMemoryTool(),
        search_exercises,
        search_food_catalog,
        log_food_entry,
        log_workout_entry,
        get_daily_summary,
        calculate_tdee_and_macro_targets,
        generate_progress_chart,
        search_online_recipes,
        generate_fitness_image,
        generate_fitness_video,
    ],
    code_executor=_code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

