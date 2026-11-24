from datetime import date, datetime, time
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatMessage, FoodItem, MealLog, Schedule, User
from app.schemas import FoodRecommendRequest, FoodRecommendResponse, ScheduleCreateRequest
from app.services.calculator import calculate_exercise_adjustments
from app.services.gemini_ai import gemini_service
from app.services.scheduler import generate_flexible_schedule

router = APIRouter(prefix="/api/recommend", tags=["Schedule, Eating Out & AI Chat"])


class FoodItemCreate(BaseModel):
    name: str
    scene_tag: str
    store_brand: str = "一般外食"
    portion_desc: str = "1 份"
    calories: int = Field(..., ge=0)
    protein_g: float = Field(default=0.0, ge=0)
    carbs_g: float = Field(default=0.0, ge=0)
    fat_g: float = Field(default=0.0, ge=0)
    tags: list[str] = Field(default_factory=list)


def _get_remaining_quota(user: User, db: Session) -> dict:
    today = date.today()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today, time.max)
    logs = (
        db.query(MealLog)
        .filter(MealLog.user_id == user.id, MealLog.logged_at >= start_dt, MealLog.logged_at <= end_dt)
        .all()
    )
    consumed_kcal = sum(l.calories for l in logs)
    consumed_p = sum(l.protein_g for l in logs)
    consumed_c = sum(l.carbs_g for l in logs)
    consumed_f = sum(l.fat_g for l in logs)

    return {
        "remaining_kcal": max(0, user.daily_calorie_target - consumed_kcal),
        "remaining_protein_g": round(max(0.0, user.protein_g - consumed_p), 1),
        "remaining_carbs_g": round(max(0.0, user.carbs_g - consumed_c), 1),
        "remaining_fat_g": round(max(0.0, user.fat_g - consumed_f), 1),
    }


@router.post("/schedule")
def create_or_update_schedule(payload: ScheduleCreateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    ex_adj = calculate_exercise_adjustments(
        weight_kg=user.weight_kg,
        selected_exercises=payload.selected_exercises,
        base_water_ml=user.water_ml,
        base_carbs_g=user.carbs_g,
    )

    slots = generate_flexible_schedule(
        shift_type=payload.shift_type,
        work_start=payload.work_start,
        work_end=payload.work_end,
        meal_windows=payload.meal_windows,
        rest_exercise_time=payload.rest_exercise_time,
        daily_calories=user.daily_calorie_target,
        daily_protein_g=user.protein_g,
        has_exercise=len(payload.selected_exercises) > 0,
    )

    schedule = Schedule(
        user_id=user.id,
        schedule_date=payload.schedule_date,
        shift_type=payload.shift_type,
        work_start=payload.work_start,
        work_end=payload.work_end,
        meal_windows=payload.meal_windows,
        rest_exercise_time=payload.rest_exercise_time,
        selected_exercises=payload.selected_exercises,
        extra_burn_kcal=ex_adj["extra_burn_kcal"],
        adjusted_water_ml=ex_adj["adjusted_water_ml"],
        adjusted_carbs_g=ex_adj["adjusted_carbs_g"],
        recommended_slots=slots,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {"schedule": schedule, "exercise_summary": ex_adj}


@router.get("/schedule/{user_id}/today")
def get_today_schedule(user_id: int, db: Session = Depends(get_db)):
    schedule = (
        db.query(Schedule)
        .filter(Schedule.user_id == user_id, Schedule.schedule_date == date.today())
        .order_by(Schedule.created_at.desc())
        .first()
    )
    return {"schedule": schedule}


@router.post("/foods")
def save_custom_food_item(payload: FoodItemCreate, db: Session = Depends(get_db)):
    """讓使用者動態新增常吃的外食單品到 SQLite（非寫死資料）。"""
    item = FoodItem(**payload.model_dump(), is_default=False)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/foods")
def list_saved_food_items(scene_tag: str | None = None, db: Session = Depends(get_db)):
    query = db.query(FoodItem)
    if scene_tag:
        query = query.filter(FoodItem.scene_tag == scene_tag)
    return {"items": query.all()}


@router.post("/eating-out", response_model=FoodRecommendResponse)
def recommend_eating_out(payload: FoodRecommendRequest, db: Session = Depends(get_db)):
    """純動態外食推薦：依剩餘額度 + 場景由 Gemini AI 即時生成，並參考使用者儲存的單品。"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    quota = _get_remaining_quota(user, db)
    saved_items = db.query(FoodItem).filter(FoodItem.scene_tag == payload.scene_tag).all()
    saved_dicts = [
        {
            "name": i.name,
            "store_brand": i.store_brand,
            "portion": i.portion_desc,
            "calories": i.calories,
            "protein_g": i.protein_g,
            "carbs_g": i.carbs_g,
            "fat_g": i.fat_g,
        }
        for i in saved_items
    ]

    try:
        combos = gemini_service.recommend_eating_out(
            remaining_kcal=quota["remaining_kcal"],
            remaining_protein_g=quota["remaining_protein_g"],
            remaining_carbs_g=quota["remaining_carbs_g"],
            remaining_fat_g=quota["remaining_fat_g"],
            scene_tag=payload.scene_tag,
            user_saved_foods=saved_dicts,
            user_preference=payload.user_preference,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 外食推薦生成失敗：{exc}") from exc

    return FoodRecommendResponse(
        scene_tag=payload.scene_tag,
        remaining_calories=quota["remaining_kcal"],
        remaining_protein_g=quota["remaining_protein_g"],
        combos=combos,
    )


@router.post("/chat")
async def chat_with_ai_assistant(
    user_id: int = Form(...),
    message: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    quota = _get_remaining_quota(user, db)
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    chat_history = [{"role": r.role, "content": r.content} for r in history_rows]

    image_bytes = await image.read() if image else None
    mime_type = image.content_type if image and image.content_type else "image/jpeg"

    user_context = {
        "nickname": user.nickname,
        "weight_kg": user.weight_kg,
        "daily_calorie_target": user.daily_calorie_target,
        "daily_protein_target_g": user.protein_g,
        **quota,
    }

    try:
        reply_text = gemini_service.chat_with_assistant(
            user_message=message,
            user_context=user_context,
            chat_history=chat_history,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    db.add(ChatMessage(user_id=user_id, role="user", content=message, has_image=image is not None))
    db.add(ChatMessage(user_id=user_id, role="model", content=reply_text, has_image=False))
    db.commit()

    return {"reply": reply_text, "remaining_quota": quota}


@router.get("/chat/{user_id}/history")
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(30)
        .all()
    )
    return {"messages": rows}