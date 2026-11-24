import { useEffect, useState } from "react";
import { Clock, Dumbbell, Check } from "lucide-react";
import { api } from "../services/api";

const EXERCISES = [
  { id: "home_bodyweight", label: "居家徒手 / 啞鈴" },
  { id: "walk_jog", label: "操場快走 / 慢跑" },
  { id: "gym_strength", label: "健身房重訓" },
  { id: "micro_stretch", label: "零碎時間伸展" },
];

export default function SchedulePage({ userId, onUpdated }) {
  const [shiftType, setShiftType] = useState("regular");
  const [workStart, setWorkStart] = useState("09:00");
  const [workEnd, setWorkEnd] = useState("18:00");
  const [selectedExercises, setSelectedExercises] = useState([]);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getTodaySchedule(userId).then((res) => {
      if (res.schedule) setPlan(res.schedule);
    }).catch(() => {});
  }, [userId]);

  const toggleExercise = (id) => {
    setSelectedExercises((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.saveSchedule({
        user_id: userId,
        shift_type: shiftType,
        work_start: workStart,
        work_end: workEnd,
        meal_windows: [],
        rest_exercise_time: "20:00",
        selected_exercises: selectedExercises,
      });
      setPlan(res.schedule);
      onUpdated();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 pb-24">
      <form onSubmit={handleSave} className="bg-white dark:bg-slate-900 rounded-3xl p-5 border border-slate-100 dark:border-slate-800 space-y-4">
        <h2 className="font-bold text-base flex items-center gap-2">
          <Clock className="w-5 h-5 text-emerald-500" /> 今日作息與輪班設定
        </h2>

        <div>
          <label className="text-xs text-slate-500">班別 / 作息模式</label>
          <select
            value={shiftType}
            onChange={(e) => setShiftType(e.target.value)}
            className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm"
          >
            <option value="regular">一般日班 / 固定作息</option>
            <option value="early">早班</option>
            <option value="late">晚班（下班較晚）</option>
            <option value="night">大夜班</option>
            <option value="flexible">彈性不固定班表</option>
            <option value="rest">休假日</option>
          </select>
        </div>

        {shiftType !== "rest" && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-500">上班 / 開始時間</label>
              <input
                type="time"
                value={workStart}
                onChange={(e) => setWorkStart(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500">下班 / 結束時間</label>
              <input
                type="time"
                value={workEnd}
                onChange={(e) => setWorkEnd(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm"
              />
            </div>
          </div>
        )}

        <div>
          <label className="text-xs text-slate-500 flex items-center gap-1.5 mb-2">
            <Dumbbell className="w-4 h-4 text-emerald-500" /> 今日運動處方（可多選）
          </label>
          <div className="grid grid-cols-2 gap-2">
            {EXERCISES.map((ex) => {
              const active = selectedExercises.includes(ex.id);
              return (
                <button
                  key={ex.id}
                  type="button"
                  onClick={() => toggleExercise(ex.id)}
                  className={`p-2.5 rounded-xl text-xs font-medium border text-left flex items-center justify-between ${
                    active
                      ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600"
                      : "border-slate-200 dark:border-slate-800"
                  }`}
                >
                  {ex.label}
                  {active && <Check className="w-3.5 h-3.5" />}
                </button>
              );
            })}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-2xl bg-emerald-500 text-white font-semibold text-sm"
        >
          {loading ? "排程計算中..." : "生成彈性進食排程"}
        </button>
      </form>

      {plan && (
        <div className="space-y-2.5">
          <div className="bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-2xl p-3.5 text-xs flex justify-between">
            <span>運動預估消耗：<b>+{plan.extra_burn_kcal} kcal</b></span>
            <span>今日建議飲水：<b>{plan.adjusted_water_ml} ml</b></span>
          </div>
          {plan.recommended_slots?.map((slot, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-100 dark:border-slate-800">
              <div className="flex justify-between items-center">
                <span className="font-bold text-sm">{slot.title}</span>
                <span className="text-xs font-semibold text-emerald-600">{slot.suggested_time}</span>
              </div>
              {slot.suggested_calories > 0 && (
                <p className="text-xs text-slate-400 mt-1">
                  建議分配：{slot.suggested_calories} kcal（約 {slot.calorie_ratio_pct}%）• 蛋白質 {slot.suggested_protein_g}g
                </p>
              )}
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-1.5">{slot.tip}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}