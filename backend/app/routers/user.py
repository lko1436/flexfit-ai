from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MealLog, Schedule, User
from app.schemas import (
    GoalOption,
    GoalSetupRequest,
    GuardrailResult,
    UserOnboardingRequest,
    UserProfileResponse,
    evaluate_weight_loss_guardrails,
)
from app.services.calculator import (
    calculate_bmi,
    calculate_daily_nutrition,
    calculate_tdee,
    estimate_bmr,
    evaluate_daily_compliance,
    generate_suggested_goals,
)

router = APIRouter(prefix="/api/user", tags=["User & Onboarding"])


def _to_profile_response(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        nickname=user.nickname,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        bmi=calculate_bmi(user.height_cm, user.weight_kg),
        gender=user.gender,
        age=user.age,
        activity_level=user.activity_level,
        goal_mode=user.goal_mode,
        goal_tier=user.goal_tier,
        target_weight_kg=user.target_weight_kg,
        target_weeks=user.target_weeks,
        daily_calorie_target=user.daily_calorie_target,
        daily_calorie_min=user.daily_calorie_min,
        daily_calorie_max=user.daily_calorie_max,
        protein_g=user.protein_g,
        carbs_g=user.carbs_g,
        fat_g=user.fat_g,
        water_ml=user.water_ml,
    )


@router.post("/onboarding")
def onboard_user(payload: UserOnboardingRequest, db: Session = Depends(get_db)):
    """極簡初始設定：僅需身高與體重即可建立檔案並取得 3 種系統建議目標。"""
    bmr = estimate_bmr(payload.weight_kg, payload.height_cm, payload.gender, payload.age)
    tdee = calculate_tdee(bmr, payload.activity_level)
    suggested_options = generate_suggested_goals(
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        gender=payload.gender,
        age=payload.age,
        activity_level=payload.activity_level,
    )
    default_opt = suggested_options[1]  # 預設先以 standard 初始化

    user = User(
        nickname=payload.nickname,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        gender=payload.gender,
        age=payload.age,
        activity_level=payload.activity_level,
        goal_mode="suggested",
        goal_tier=default_opt.tier,
        target_weight_kg=default_opt.target_weight_kg,
        target_weeks=default_opt.target_weeks,
        daily_calorie_target=default_opt.daily_calorie_target,
        daily_calorie_min=default_opt.daily_calorie_range[0],
        daily_calorie_max=default_opt.daily_calorie_range[1],
        protein_g=default_opt.protein_g,
        carbs_g=default_opt.carbs_g,
        fat_g=default_opt.fat_g,
        water_ml=default_opt.water_ml,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user": _to_profile_response(user),
        "estimated_bmr": round(bmr),
        "estimated_tdee": tdee,
        "suggested_goals": suggested_options,
    }


@router.get("/{user_id}/goal-options", response_model=list[GoalOption])
def get_goal_options(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")
    return generate_suggested_goals(
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        gender=user.gender,
        age=user.age,
        activity_level=user.activity_level,
    )


@router.post("/{user_id}/goal")
def set_user_goal(user_id: int, payload: GoalSetupRequest, db: Session = Depends(get_db)):
    """
    目標設定雙模式 + 健康防呆驗證 (Guardrails)。
    若自訂減重速度過快且未強制覆寫，回傳 applied=False 與建議週數供一鍵套用。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    if payload.mode == "suggested":
        options = generate_suggested_goals(
            user.height_cm, user.weight_kg, user.gender, user.age, user.activity_level
        )
        chosen = next((opt for opt in options if opt.tier == payload.tier), options[1])
        user.goal_mode = "suggested"
        user.goal_tier = chosen.tier
        user.target_weight_kg = chosen.target_weight_kg
        user.target_weeks = chosen.target_weeks
        user.daily_calorie_target = chosen.daily_calorie_target
        user.daily_calorie_min = chosen.daily_calorie_range[0]
        user.daily_calorie_max = chosen.daily_calorie_range[1]
        user.protein_g = chosen.protein_g
        user.carbs_g = chosen.carbs_g
        user.fat_g = chosen.fat_g
        user.water_ml = chosen.water_ml
        db.commit()
        db.refresh(user)
        return {
            "applied": True,
            "guardrail": GuardrailResult(is_safe=True, severity="ok"),
            "user": _to_profile_response(user),
        }

    # Custom mode -> 執行健康防呆驗證
    assert payload.target_weight_kg is not None and payload.target_weeks is not None
    guardrail = evaluate_weight_loss_guardrails(
        current_weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        target_weight_kg=payload.target_weight_kg,
        target_weeks=payload.target_weeks,
    )

    if not guardrail.is_safe and not payload.force_override:
        return {
            "applied": False,
            "guardrail": guardrail,
            "user": _to_profile_response(user),
        }

    bmr = estimate_bmr(user.weight_kg, user.height_cm, user.gender, user.age)
    tdee = calculate_tdee(bmr, user.activity_level)
    weekly_loss = max(0.0, (user.weight_kg - payload.target_weight_kg) / payload.target_weeks)
    nutrition = calculate_daily_nutrition(user.weight_kg, tdee, weekly_loss)

    user.goal_mode = "custom"
    user.goal_tier = None
    user.target_weight_kg = payload.target_weight_kg
    user.target_weeks = payload.target_weeks
    user.daily_calorie_target = nutrition["daily_calorie_target"]
    user.daily_calorie_min = nutrition["daily_calorie_min"]
    user.daily_calorie_max = nutrition["daily_calorie_max"]
    user.protein_g = nutrition["protein_g"]
    user.carbs_g = nutrition["carbs_g"]
    user.fat_g = nutrition["fat_g"]
    user.water_ml = nutrition["water_ml"]

    db.commit()
    db.refresh(user)
    return {
        "applied": True,
        "guardrail": guardrail,
        "user": _to_profile_response(user),
    }


@router.get("/{user_id}/dashboard")
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    """首頁儀表板總覽：剩餘熱量、營養素、飲水與今日排程。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    today = date.today()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today, time.max)

    logs = (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id, MealLog.logged_at >= start_dt, MealLog.logged_at <= end_dt)
        .order_by(MealLog.logged_at.desc())
        .all()
    )

    consumed_kcal = sum(log.calories for log in logs)
    consumed_protein = round(sum(log.protein_g for log in logs), 1)
    consumed_carbs = round(sum(log.carbs_g for log in logs), 1)
    consumed_fat = round(sum(log.fat_g for log in logs), 1)

    today_schedule = (
        db.query(Schedule)
        .filter(Schedule.user_id == user_id, Schedule.schedule_date == today)
        .order_by(Schedule.created_at.desc())
        .first()
    )

    target_water = today_schedule.adjusted_water_ml if today_schedule else user.water_ml
    target_carbs = today_schedule.adjusted_carbs_g if today_schedule else user.carbs_g

    return {
        "user": _to_profile_response(user),
        "today_summary": {
            "consumed_calories": consumed_kcal,
            "remaining_calories": max(0, user.daily_calorie_target - consumed_kcal),
            "consumed_protein_g": consumed_protein,
            "remaining_protein_g": round(max(0.0, user.protein_g - consumed_protein), 1),
            "consumed_carbs_g": consumed_carbs,
            "target_carbs_g": target_carbs,
            "consumed_fat_g": consumed_fat,
            "target_water_ml": target_water,
            "compliance": evaluate_daily_compliance(consumed_kcal, user.daily_calorie_target),
        },
        "today_schedule": today_schedule,
        "recent_meals": logs,
    }