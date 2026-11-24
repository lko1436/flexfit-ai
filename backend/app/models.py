from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50), default="飲控夥伴")

    # 極簡必填欄位
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    # 選填微調欄位（不強制輸入）
    gender: Mapped[str] = mapped_column(String(20), default="unspecified")  # male | female | unspecified
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activity_level: Mapped[str] = mapped_column(String(20), default="light")  # sedentary | light | moderate | active

    # 目標設定
    goal_mode: Mapped[str] = mapped_column(String(20), default="suggested")  # suggested | custom
    goal_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)  # comfort | standard | lean
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 動態計算之每日目標
    daily_calorie_target: Mapped[int] = mapped_column(Integer, default=1800)
    daily_calorie_min: Mapped[int] = mapped_column(Integer, default=1620)  # -10% 彈性區間
    daily_calorie_max: Mapped[int] = mapped_column(Integer, default=1980)  # +10% 彈性區間
    protein_g: Mapped[int] = mapped_column(Integer, default=120)
    carbs_g: Mapped[int] = mapped_column(Integer, default=180)
    fat_g: Mapped[int] = mapped_column(Integer, default=60)
    water_ml: Mapped[int] = mapped_column(Integer, default=2100)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    schedules: Mapped[list["Schedule"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meal_logs: Mapped[list["MealLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    schedule_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)

    # 支援輪班 / 早晚班 / 不固定班表
    shift_type: Mapped[str] = mapped_column(String(30), default="regular")  # regular | early | late | night | flexible | rest
    work_start: Mapped[str | None] = mapped_column(String(10), nullable=True)  # e.g. "09:00"
    work_end: Mapped[str | None] = mapped_column(String(10), nullable=True)    # e.g. "18:00"
    meal_windows: Mapped[list[str]] = mapped_column(JSON, default=list)        # e.g. ["12:00-13:00", "19:30-20:30"]
    rest_exercise_time: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "20:00"

    # 多選運動處方與動態調整結果
    selected_exercises: Mapped[list[str]] = mapped_column(JSON, default=list)
    extra_burn_kcal: Mapped[int] = mapped_column(Integer, default=0)
    adjusted_water_ml: Mapped[int] = mapped_column(Integer, default=2100)
    adjusted_carbs_g: Mapped[int] = mapped_column(Integer, default=180)
    recommended_slots: Mapped[list[dict]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="schedules")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    meal_slot: Mapped[str] = mapped_column(String(30), default="flexible")  # breakfast | lunch | dinner | snack | flexible
    source_type: Mapped[str] = mapped_column(String(20), default="manual")  # photo | text | manual
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    food_name: Mapped[str] = mapped_column(String(120), nullable=False)
    portion_desc: Mapped[str] = mapped_column(String(120), default="1 份")
    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0.0)
    fat_g: Mapped[float] = mapped_column(Float, default=0.0)

    ai_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="meal_logs")


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    scene_tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # 場景標籤: convenience_store | breakfast_shop | bento_buffet | luwei_salty_chicken | fast_food | beverage_sugar_free
    store_brand: Mapped[str] = mapped_column(String(50), default="一般外食")
    portion_desc: Mapped[str] = mapped_column(String(80), default="1 份")

    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0.0)
    fat_g: Mapped[float] = mapped_column(Float, default=0.0)

    tags: Mapped[list[str]] = mapped_column(JSON, default=list)  # e.g. ["高蛋白", "低脂", "微波即食"]
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | model
    content: Mapped[str] = mapped_column(Text, nullable=False)
    has_image: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="chat_messages")