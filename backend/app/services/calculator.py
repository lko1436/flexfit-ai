import math
from app.schemas import GoalOption

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,   # 久坐少動
    "light": 1.375,     # 輕度活動 / 一般通勤（預設）
    "moderate": 1.55,   # 中度活動 / 每週運動 3-4 天
    "active": 1.725,    # 高度活動 / 體力勞動或每日訓練
}

# 運動處方預設參數 (MET 值與預設時長)
EXERCISE_PRESETS = {
    "home_bodyweight": {"label": "居家徒手 / 啞鈴訓練", "met": 4.5, "duration_min": 35, "carb_boost_g": 15, "water_boost_ml": 350},
    "walk_jog": {"label": "操場快走 / 慢跑", "met": 6.0, "duration_min": 40, "carb_boost_g": 25, "water_boost_ml": 500},
    "gym_strength": {"label": "健身房重訓", "met": 5.5, "duration_min": 50, "carb_boost_g": 30, "water_boost_ml": 550},
    "micro_stretch": {"label": "零碎時間伸展 / 活動", "met": 2.5, "duration_min": 20, "carb_boost_g": 0, "water_boost_ml": 200},
}


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m ** 2), 1)


def estimate_bmr(
    weight_kg: float,
    height_cm: float,
    gender: str = "unspecified",
    age: int | None = None,
) -> float:
    """
    使用 Mifflin-St Jeor 公式計算基礎代謝率 (BMR)。
    若使用者未填寫性別與年齡，採用中性中間值 (常數 -78, 年齡預設 30 歲) 進行合理估算。
    """
    effective_age = age if age is not None else 30
    base = 10 * weight_kg + 6.25 * height_cm - 5 * effective_age

    if gender == "male":
        return base + 5
    if gender == "female":
        return base - 161
    return base - 78  # 中性無偏估計


def calculate_tdee(bmr: float, activity_level: str = "light") -> int:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    return round(bmr * multiplier)


def calculate_daily_nutrition(
    weight_kg: float,
    tdee: int,
    weekly_loss_kg: float,
    protein_factor: float = 1.6,
) -> dict:
    """
    依據 TDEE 與每週預期減重幅度計算每日熱量赤字與巨量營養素。
    1 kg 脂肪約等於 7700 kcal；設定安全下限避免低於基礎代謝過多。
    """
    daily_deficit = round((weekly_loss_kg * 7700) / 7)
    raw_target = tdee - daily_deficit
    safe_floor = max(1200, round(weight_kg * 18))
    calorie_target = max(safe_floor, raw_target)

    # 彈性達標區間 (±10%)
    calorie_min = round(calorie_target * 0.90)
    calorie_max = round(calorie_target * 1.10)

    # 蛋白質優先保留肌肉 (1.6 ~ 2.0 g/kg)
    protein_g = round(weight_kg * protein_factor)
    protein_kcal = protein_g * 4

    # 脂肪佔總熱量 25%（維持荷爾蒙健康）
    fat_kcal = round(calorie_target * 0.25)
    fat_g = max(35, round(fat_kcal / 9))

    # 碳水化合物補齊剩餘熱量
    remaining_kcal = max(200, calorie_target - protein_kcal - (fat_g * 9))
    carbs_g = round(remaining_kcal / 4)

    # 每日基礎飲水量：體重(kg) * 35 ml
    water_ml = round((weight_kg * 35) / 50) * 50

    return {
        "daily_calorie_target": calorie_target,
        "daily_calorie_min": calorie_min,
        "daily_calorie_max": calorie_max,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "water_ml": water_ml,
    }


def generate_suggested_goals(
    height_cm: float,
    weight_kg: float,
    gender: str = "unspecified",
    age: int | None = None,
    activity_level: str = "light",
) -> list[GoalOption]:
    """
    根據身高體重自動產出 3 種健康減脂目標方案：
    1. comfort: 微幅減脂舒適型
    2. standard: 標準健康理想型
    3. lean: 進階精實型
    """
    bmr = estimate_bmr(weight_kg, height_cm, gender, age)
    tdee = calculate_tdee(bmr, activity_level)
    height_m = height_cm / 100.0

    # 參考健康理想 BMI (21.5) 與減重底線 (BMI 19.0)
    ideal_bmi_weight = round(21.5 * (height_m ** 2), 1)
    min_healthy_weight = round(19.0 * (height_m ** 2), 1)

    configs = [
        {
            "tier": "comfort",
            "title": "微幅減脂舒適型",
            "subtitle": "幾乎無痛感，適合外食族或剛起步建立習慣",
            "loss_pct": 0.04,       # 減去約 4% 體重
            "weekly_rate": 0.005,   # 每週 0.5%
            "protein_factor": 1.5,
        },
        {
            "tier": "standard",
            "title": "標準健康理想型",
            "subtitle": "兼顧減脂效率與生活品質，最推薦的永續節奏",
            "loss_pct": 0.08,       # 減去約 8% 體重或往理想 BMI 邁進
            "weekly_rate": 0.008,   # 每週 0.8%
            "protein_factor": 1.7,
        },
        {
            "tier": "lean",
            "title": "進階精實型",
            "subtitle": "較積極的熱量赤字與高蛋白配置，適合有運動習慣者",
            "loss_pct": 0.12,       # 減去約 12% 體重
            "weekly_rate": 0.011,   # 每週 1.1%（仍在 1.5% 安全線內）
            "protein_factor": 1.9,
        },
    ]

    options: list[GoalOption] = []
    for cfg in configs:
        raw_target = round(weight_kg * (1 - cfg["loss_pct"]), 1)
        if cfg["tier"] == "standard" and weight_kg > ideal_bmi_weight + 3:
            raw_target = max(ideal_bmi_weight, raw_target)
        target_weight = max(min_healthy_weight, raw_target)

        if target_weight >= weight_kg:
            # 若使用者已經很瘦，提供輕微體態微調選項
            target_weight = round(max(min_healthy_weight, weight_kg - 1.5), 1)

        weekly_loss = round(weight_kg * cfg["weekly_rate"], 2)
        weeks = max(4, math.ceil((weight_kg - target_weight) / max(weekly_loss, 0.25)))
        actual_weekly_loss = round((weight_kg - target_weight) / weeks, 2)

        nutrition = calculate_daily_nutrition(
            weight_kg=weight_kg,
            tdee=tdee,
            weekly_loss_kg=actual_weekly_loss,
            protein_factor=cfg["protein_factor"],
        )

        options.append(
            GoalOption(
                tier=cfg["tier"],
                title=cfg["title"],
                subtitle=cfg["subtitle"],
                target_weight_kg=target_weight,
                target_weeks=weeks,
                weekly_loss_kg=actual_weekly_loss,
                daily_calorie_target=nutrition["daily_calorie_target"],
                daily_calorie_range=(nutrition["daily_calorie_min"], nutrition["daily_calorie_max"]),
                protein_g=nutrition["protein_g"],
                carbs_g=nutrition["carbs_g"],
                fat_g=nutrition["fat_g"],
                water_ml=nutrition["water_ml"],
            )
        )

    return options


def calculate_exercise_adjustments(
    weight_kg: float,
    selected_exercises: list[str],
    base_water_ml: int,
    base_carbs_g: int,
) -> dict:
    """
    依據使用者多選的運動處方，計算預估消耗熱量，並動態微調當日飲水與碳水建議。
    公式：Calories = MET * weight_kg * (duration_min / 60)
    """
    total_burn = 0
    water_boost = 0
    carb_boost = 0
    labels = []

    for ex_key in selected_exercises:
        preset = EXERCISE_PRESETS.get(ex_key)
        if not preset:
            continue
        burn = round(preset["met"] * weight_kg * (preset["duration_min"] / 60))
        total_burn += burn
        water_boost += preset["water_boost_ml"]
        carb_boost += preset["carb_boost_g"]
        labels.append(preset["label"])

    # 飲水與碳水微調設定合理上限，避免重複疊加過高
    adjusted_water_ml = base_water_ml + min(water_boost, 1000)
    adjusted_carbs_g = base_carbs_g + min(carb_boost, 50)

    return {
        "selected_labels": labels,
        "extra_burn_kcal": total_burn,
        "adjusted_water_ml": adjusted_water_ml,
        "adjusted_carbs_g": adjusted_carbs_g,
    }


def evaluate_daily_compliance(consumed_kcal: int, target_kcal: int, tolerance: float = 0.10) -> dict:
    """彈性達標制：落在目標 ±10% 區間即判定為達標。"""
    low = round(target_kcal * (1 - tolerance))
    high = round(target_kcal * (1 + tolerance))

    if low <= consumed_kcal <= high:
        status = "on_track"
        message = "今日熱量落在彈性達標區間內，表現很棒！"
    elif consumed_kcal < low:
        status = "under"
        message = f"距離達標下限還有 {low - consumed_kcal} kcal，記得補充足夠蛋白質與營養喔。"
    else:
        status = "over"
        message = f"略高於區間 {consumed_kcal - high} kcal，沒關係！明天多喝水、稍微活動即可平衡。"

    return {
        "status": status,
        "target_range": [low, high],
        "consumed_kcal": consumed_kcal,
        "message": message,
    }