from datetime import datetime, timedelta


def _parse_hhmm(time_str: str | None, fallback: str) -> datetime:
    target = time_str or fallback
    try:
        return datetime.strptime(target, "%H:%M")
    except ValueError:
        return datetime.strptime(fallback, "%H:%M")


def _fmt_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def generate_flexible_schedule(
    shift_type: str,
    work_start: str | None,
    work_end: str | None,
    meal_windows: list[str],
    rest_exercise_time: str | None,
    daily_calories: int,
    daily_protein_g: int,
    has_exercise: bool = False,
) -> list[dict]:
    """
    根據作息（含輪班/早晚班/不固定班表）自動推算「最佳進食時間點」與「熱量分配比例」，
    不強制幾點前不能吃，而是給予不勉強的彈性建議。
    """
    if shift_type == "rest":
        slots = [
            ("睡醒第一餐（早午餐）", "10:30", 0.35, "優質蛋白質 + 複合碳水（如地瓜、全麥吐司），穩定整天血糖"),
            ("下午彈性餐", "15:30", 0.35, "均衡正餐，優先選擇原型食物與蔬菜"),
            ("晚間輕食餐", "20:00", 0.30, "高蛋白低負擔為主，睡前 2 小時完成即可"),
        ]
    elif shift_type == "night":
        start_dt = _parse_hhmm(work_start, "22:00")
        pre_work = _fmt_hhmm(start_dt - timedelta(hours=1, minutes=30))
        mid_shift = _fmt_hhmm(start_dt + timedelta(hours=4))
        post_work = _fmt_hhmm(start_dt + timedelta(hours=9))
        slots = [
            ("上工前能量餐", pre_work, 0.35, "高蛋白 + 複合碳水，支撐夜班專注力"),
            ("班中空檔補給", mid_shift, 0.40, "方便取得的原型食物或超商高蛋白組合，避免高油炸物"),
            ("下班睡前輕食", post_work, 0.25, "輕量化高蛋白（如無糖豆漿、雞胸、蒸蛋），好消化不影響睡眠"),
        ]
    elif shift_type == "late":
        start_dt = _parse_hhmm(work_start, "14:00")
        end_dt = _parse_hhmm(work_end, "23:00")
        pre_work = _fmt_hhmm(start_dt - timedelta(hours=1))
        mid_shift = _fmt_hhmm(start_dt + timedelta(hours=4, minutes=30))
        post_work = _fmt_hhmm(end_dt + timedelta(minutes=30))
        slots = [
            ("班前早午餐", pre_work, 0.35, "高蛋白搭配適量碳水，讓晚班前半段不易嘴饞"),
            ("晚餐空檔餐", mid_shift, 0.40, "若時間緊湊可選便當去皮或健康餐盒，補齊蔬菜與蛋白質"),
            ("下班輕量化蛋白餐", post_work, 0.25, "下班較晚時建議以湯品、豆腐、魚肉或高蛋白飲為主，不勉強挨餓"),
        ]
    else:
        # regular / early / flexible
        start_dt = _parse_hhmm(work_start, "09:00")
        end_dt = _parse_hhmm(work_end, "18:00")
        pre_work = _fmt_hhmm(start_dt - timedelta(minutes=45))
        lunch_time = meal_windows[0].split("-")[0].strip() if meal_windows else _fmt_hhmm(start_dt + timedelta(hours=3, minutes=30))
        dinner_time = _fmt_hhmm(end_dt + timedelta(hours=1))
        slots = [
            ("工作前啟動餐", pre_work, 0.30, "高蛋白 + 適量碳水（如茶葉蛋 + 無糖拿鐵/地瓜），提升專注力"),
            ("午間主力餐", lunch_time, 0.40, "外食最容易吃飽的一餐，優先夾足蛋白質與兩拳頭蔬菜"),
            ("下班彈性晚餐", dinner_time, 0.30, "依當天剩餘扣打彈性調整；若已運動可適度補充碳水幫助恢復"),
        ]

    result = []
    for title, suggested_time, ratio, tip in slots:
        kcal = round(daily_calories * ratio)
        protein = round(daily_protein_g * ratio)
        result.append(
            {
                "title": title,
                "suggested_time": suggested_time,
                "calorie_ratio_pct": round(ratio * 100),
                "suggested_calories": kcal,
                "suggested_protein_g": protein,
                "tip": tip,
            }
        )

    if has_exercise and rest_exercise_time:
        result.append(
            {
                "title": "運動後黃金補給（彈性）",
                "suggested_time": rest_exercise_time,
                "calorie_ratio_pct": 0,
                "suggested_calories": 0,
                "suggested_protein_g": 20,
                "tip": "已為您微調今日飲水與碳水額度，運動後記得補水與一份快速蛋白質即可，不必額外強迫進食。",
            }
        )

    return result