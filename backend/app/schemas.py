import math
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


# --- 1. 極簡初始設定與目標防呆 (Onboarding & Guardrails) ---

class UserOnboardingRequest(BaseModel):
    nickname: str = Field(default="飲控夥伴", max_length=50)
    height_cm: float = Field(..., gt=100, lt=250, description="目前身高 (cm)")
    weight_kg: float = Field(..., gt=30, lt=300, description="目前體重 (kg)")
    gender: Literal["male", "female", "unspecified"] = Field(default="unspecified", description="選填性別")
    age: int | None = Field(default=None, ge=15, le=90, description="選填年齡")
    activity_level: Literal["sedentary", "light", "moderate", "active"] = Field(default="light")


class GoalOption(BaseModel):
    tier: Literal["comfort", "standard", "lean"]
    title: str
    subtitle: str
    target_weight_kg: float
    target_weeks: int
    weekly_loss_kg: float
    daily_calorie_target: int
    daily_calorie_range: tuple[int, int]
    protein_g: int
    carbs_g: int
    fat_g: int
    water_ml: int


class GuardrailResult(BaseModel):
    is_safe: bool
    severity: Literal["ok", "warning", "blocked"]
    warnings: list[str] = Field(default_factory=list)
    recommended_weeks: int | None = None
    recommended_weekly_loss_kg: float | None = None
    one_click_message: str | None = None


class GoalSetupRequest(BaseModel):
    mode: Literal["suggested", "custom"]
    tier: Literal["comfort", "standard", "lean"] | None = None
    target_weight_kg: float | None = Field(default=None, gt=30, lt=250)
    target_weeks: int | None = Field(default=None, ge=1, le=156)
    force_override: bool = Field(default=False, description="使用者確認風險後是否仍套用")

    @model_validator(mode="after")
    def validate_mode_fields(self) -> "GoalSetupRequest":
        if self.mode == "suggested" and self.tier is None:
            raise ValueError("選擇系統建議體位時，必須指定 tier (comfort / standard / lean)。")
        if self.mode == "custom" and (self.target_weight_kg is None or self.target_weeks is None):
            raise ValueError("選擇自訂目標時，必須提供目標體重與預計達成週數。")
        return self


def evaluate_weight_loss_guardrails(
    current_weight_kg: float,
    height_cm: float,
    target_weight_kg: float,
    target_weeks: int,
) -> GuardrailResult:
    """
    核心健康防呆驗證：
    1. 每週減重超過體重 1.5% -> 攔截並發出柔性警告
    2. 每週減重超過 2.5 kg（相當於一個月瘦超過 10 kg）-> 攔截並發出柔性警告
    3. 目標體重導致 BMI < 18.5（過輕）-> 發出健康提醒
    並自動換算「最健康的建議達成週數」供前端一鍵套用。
    """
    weight_diff = current_weight_kg - target_weight_kg
    if weight_diff <= 0:
        return GuardrailResult(is_safe=True, severity="ok")

    weekly_loss = weight_diff / target_weeks
    max_safe_weekly_pct = current_weight_kg * 0.015  # 每週體重 1.5% 上限
    max_safe_weekly_abs = 2.5                        # 相當於月瘦 10kg 上限
    ideal_weekly_loss = min(current_weight_kg * 0.008, 0.9)  # 健康舒適基準：每週約 0.8% 體重（上限 0.9kg/週）

    height_m = height_cm / 100.0
    target_bmi = target_weight_kg / (height_m ** 2)

    warnings: list[str] = []
    is_too_fast = (weekly_loss > max_safe_weekly_pct) or (weekly_loss > max_safe_weekly_abs)

    if weekly_loss > max_safe_weekly_abs:
        warnings.append(
            f"目前設定每週需減重 {weekly_loss:.2f} kg（相當於一個月超過 {weekly_loss * 4:.1f} kg），"
            "屬於極端快速減重，極易造成大量肌肉流失、基礎代謝率受損與復胖反彈。"
        )
    elif weekly_loss > max_safe_weekly_pct:
        warnings.append(
            f"目前設定每週減重 {weekly_loss:.2f} kg（超過目前體重的 1.5%），"
            "速度偏快，可能增加肌肉流失、疲勞與荷爾蒙代謝失衡的風險。"
        )

    if target_bmi < 18.5:
        warnings.append(
            f"目標體重 {target_weight_kg:.1f} kg 對應的 BMI 為 {target_bmi:.1f}（低於健康標準 18.5），"
            "建議以體脂下降與維持肌力為主，不建議追求過低體重。"
        )

    if not warnings:
        return GuardrailResult(is_safe=True, severity="ok")

    recommended_weeks = max(1, math.ceil(weight_diff / max(ideal_weekly_loss, 0.35)))
    rec_weekly = round(weight_diff / recommended_weeks, 2)

    return GuardrailResult(
        is_safe=False,
        severity="blocked" if is_too_fast else "warning",
        warnings=warnings,
        recommended_weeks=recommended_weeks,
        recommended_weekly_loss_kg=rec_weekly,
        one_click_message=f"建議調整為 {recommended_weeks} 週達成（每週健康減重約 {rec_weekly} kg），保留肌肉不傷代謝！",
    )


class UserProfileResponse(BaseModel):
    id: int
    nickname: str
    height_cm: float
    weight_kg: float
    bmi: float
    gender: str
    age: int | None
    activity_level: str
    goal_mode: str
    goal_tier: str | None
    target_weight_kg: float | None
    target_weeks: int | None
    daily_calorie_target: int
    daily_calorie_min: int
    daily_calorie_max: int
    protein_g: int
    carbs_g: int
    fat_g: int
    water_ml: int

    model_config = {"from_attributes": True}


# --- 2. 飲食紀錄與 AI 視覺辨識 (Meals & AI Vision) ---

class MealAnalysisResponse(BaseModel):
    food_name: str = Field(..., description="辨識出的菜色名稱")
    estimated_portion: str = Field(..., description="估算份量，例如：1 碗 / 2 顆")
    calories: int = Field(..., ge=0, description="估算總熱量 (kcal)")
    protein_g: float = Field(..., ge=0, description="蛋白質 (g)")
    carbs_g: float = Field(..., ge=0, description="碳水化合物 (g)")
    fat_g: float = Field(..., ge=0, description="脂肪 (g)")
    confidence: Literal["high", "medium", "low"] = "medium"
    notes: str = Field(default="", description="營養簡評或份量提醒")


class MealLogCreate(BaseModel):
    user_id: int
    meal_slot: Literal["breakfast", "lunch", "dinner", "snack", "flexible"] = "flexible"
    source_type: Literal["photo", "text", "manual"] = "manual"
    raw_input: str | None = None
    food_name: str
    portion_desc: str = "1 份"
    calories: int = Field(..., ge=0)
    protein_g: float = Field(default=0.0, ge=0)
    carbs_g: float = Field(default=0.0, ge=0)
    fat_g: float = Field(default=0.0, ge=0)
    ai_confidence: str | None = None
    notes: str | None = None


class MealLogResponse(MealLogCreate):
    id: int
    logged_at: datetime

    model_config = {"from_attributes": True}


# --- 3. 作息排程與運動處方 (Schedule & Exercise) ---

class ScheduleCreateRequest(BaseModel):
    user_id: int
    schedule_date: date = Field(default_factory=date.today)
    shift_type: Literal["regular", "early", "late", "night", "flexible", "rest"] = "regular"
    work_start: str | None = Field(default="09:00", description="HH:MM")
    work_end: str | None = Field(default="18:00", description="HH:MM")
    meal_windows: list[str] = Field(default_factory=list, description="例如 ['12:00-13:00', '19:00-20:00']")
    rest_exercise_time: str | None = Field(default="19:30")
    selected_exercises: list[Literal["home_bodyweight", "walk_jog", "gym_strength", "micro_stretch"]] = Field(
        default_factory=list
    )


# --- 4. 動態外食推薦與 AI 聊天助手 (Recommender & Chat) ---

class FoodRecommendRequest(BaseModel):
    user_id: int
    scene_tag: Literal[
        "convenience_store",
        "breakfast_shop",
        "bento_buffet",
        "luwei_salty_chicken",
        "fast_food",
        "beverage_sugar_free",
    ]
    user_preference: str | None = Field(default=None, description="額外需求，例如：不想吃太飽、預算150元內")


class EatingOutCombo(BaseModel):
    combo_title: str
    items: list[str]
    total_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    why_it_fits: str


class FoodRecommendResponse(BaseModel):
    scene_tag: str
    remaining_calories: int
    remaining_protein_g: float
    combos: list[EatingOutCombo]


class ChatRequest(BaseModel):
    user_id: int
    message: str