from datetime import date, datetime, time
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MealLog, User
from app.schemas import MealAnalysisResponse, MealLogCreate, MealLogResponse
from app.services.gemini_ai import gemini_service

router = APIRouter(prefix="/api/meals", tags=["Meals & AI Vision"])


class TextParseRequest(BaseModel):
    text: str


@router.post("/analyze-photo", response_model=MealAnalysisResponse)
async def analyze_meal_photo(
    file: UploadFile = File(...),
    user_hint: str | None = Form(default=None),
):
    """拍照辨識：上傳食物照片，回傳 AI 估算之熱量與三大營養素 JSON。"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="請上傳有效的圖片檔案 (JPEG / PNG / WebP)。")

    image_bytes = await file.read()
    try:
        return gemini_service.analyze_food_image(
            image_bytes=image_bytes,
            mime_type=file.content_type,
            user_hint=user_hint,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 圖片辨識失敗：{exc}") from exc


@router.post("/parse-text", response_model=MealAnalysisResponse)
def parse_meal_text(payload: TextParseRequest):
    """文字快速輸入：例如「超商無糖豆漿一瓶 + 茶葉蛋兩顆」自動解析營養素。"""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="請輸入食物描述文字。")
    try:
        return gemini_service.parse_food_text(payload.text.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI 文字解析失敗：{exc}") from exc


@router.post("/log", response_model=MealLogResponse)
def create_meal_log(payload: MealLogCreate, db: Session = Depends(get_db)):
    """一鍵儲存確認後的飲食紀錄。"""
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到該使用者")

    log = MealLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/{user_id}/today", response_model=list[MealLogResponse])
def list_today_meals(user_id: int, db: Session = Depends(get_db)):
    today = date.today()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today, time.max)
    return (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id, MealLog.logged_at >= start_dt, MealLog.logged_at <= end_dt)
        .order_by(MealLog.logged_at.desc())
        .all()
    )


@router.delete("/{log_id}")
def delete_meal_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(MealLog).filter(MealLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="找不到該筆飲食紀錄")
    db.delete(log)
    db.commit()
    return {"deleted": True, "log_id": log_id}