#!/usr/bin/env python3
"""Seed initial exercises and healthy recipes/foods into Firestore for FitCoach AI."""

from google.cloud import firestore

# Hardcode the GCP Project ID string to avoid project number issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-04-ae86f5e8c9de"

def seed():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")

    # 1. Seed Exercises Catalog
    exercises = [
        {
            "name": "Barbell Squat (深蹲)",
            "category": "Legs",
            "target_muscles": ["Quadriceps", "Glutes"],
            "difficulty": "Intermediate",
            "est_burn_rate_kcal_min": 8.5,
            "instructions": "雙腳與肩同寬，背部打直核心收緊，下蹲至大腿與地面平行或略低。",
        },
        {
            "name": "Bench Press (臥推)",
            "category": "Chest",
            "target_muscles": ["Pectorals", "Triceps", "Anterior Deltoid"],
            "difficulty": "Intermediate",
            "est_burn_rate_kcal_min": 7.0,
            "instructions": "仰臥於握推椅上，雙腳踩實地面，肩胛骨後收下壓，槓鈴下放至胸口後穩定推起。",
        },
        {
            "name": "Outdoor Jogging (戶外跑步)",
            "category": "Cardio",
            "target_muscles": ["Cardiovascular", "Calves", "Hamstrings"],
            "difficulty": "Beginner",
            "est_burn_rate_kcal_min": 10.0,
            "instructions": "保持穩定配速（約6-7分速），抬頭挺胸，步伐輕快著地。",
        },
        {
            "name": "Deadlift (硬舉)",
            "category": "Back & Posterior Chain",
            "target_muscles": ["Hamstrings", "Glutes", "Erector Spinae"],
            "difficulty": "Advanced",
            "est_burn_rate_kcal_min": 9.0,
            "instructions": "槓鈴貼近小腿，屈髖俯身握槓，以臀部與腿後側發力將槓鈴拉起站直。",
        },
        {
            "name": "HIIT Burpees (波比跳)",
            "category": "Full Body / HIIT",
            "target_muscles": ["Full Body", "Cardiovascular"],
            "difficulty": "Intermediate",
            "est_burn_rate_kcal_min": 12.0,
            "instructions": "下蹲雙手觸地，雙腳後躍呈伏地挺身姿勢，迅速收腹屈腿並垂直跳起擊掌。",
        }
    ]

    for item in exercises:
        doc_id = item["name"].split()[0].lower()
        db.collection("exercises").document(doc_id).set(item)
        print(f"✓ Seeded exercise: {item['name']}")

    # 2. Seed Common Food & Nutrition Catalog
    foods = [
        {
            "name": "煎鮭魚佐花椰菜糙米飯",
            "portion": "1 份 (約 350g)",
            "calories": 520.0,
            "protein_g": 38.0,
            "carbs_g": 48.0,
            "fat_g": 18.0,
            "category": "Healthy Meal",
            "tips": "豐富 Omega-3 脂肪酸與高蛋白，極適合重訓後補充。",
        },
        {
            "name": "舒肥義式嫩雞胸肉",
            "portion": "1 片 (約 150g)",
            "calories": 165.0,
            "protein_g": 35.0,
            "carbs_g": 1.0,
            "fat_g": 2.5,
            "category": "Protein Source",
            "tips": "超低脂肪高蛋白質，減脂增肌必備主食。",
        },
        {
            "name": "無糖高纖豆漿",
            "portion": "1 瓶 (400ml)",
            "calories": 136.0,
            "protein_g": 14.0,
            "carbs_g": 8.0,
            "fat_g": 6.0,
            "category": "Beverage",
            "tips": "植物性蛋白良好來源，高飽足感。",
        },
        {
            "name": "地瓜佐水煮蛋",
            "portion": "中地瓜1顆 + 水煮蛋1顆",
            "calories": 240.0,
            "protein_g": 8.5,
            "carbs_g": 38.0,
            "fat_g": 5.5,
            "category": "Pre-Workout Snack",
            "tips": "優質低 GI 複合碳水化合物，適合運動前 1 小時補充能量。",
        }
    ]

    for item in foods:
        doc_id = item["name"][:10].replace(" ", "_")
        db.collection("food_items").document(doc_id).set(item)
        print(f"✓ Seeded food item: {item['name']}")

    print("\n✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed()
