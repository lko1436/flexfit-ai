import { Trash2, Droplets, Flame } from "lucide-react";
import ProgressRing from "../components/ProgressRing";
import { api } from "../services/api";

export default function DashboardPage({ data, onRefresh }) {
  if (!data) return null;
  const { user, today_summary: s, recent_meals: meals } = data;

  const handleDelete = async (id) => {
    await api.deleteMeal(id);
    onRefresh();
  };

  return (
    <div className="space-y-4 pb-24">
      {/* 彈性達標狀態卡 */}
      <div className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-3xl p-5 shadow-lg shadow-emerald-500/20">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs opacity-85">今日彈性目標區間 (±10%)</p>
            <h2 className="text-2xl font-bold mt-0.5">
              {user.daily_calorie_min} ~ {user.daily_calorie_max} kcal
            </h2>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-white/20 text-xs font-medium">
            {s.compliance.status === "on_track" ? "✨ 已達標" : "彈性進行中"}
          </span>
        </div>
        <p className="text-xs mt-3 bg-black/15 rounded-xl px-3 py-2">{s.compliance.message}</p>
      </div>

      {/* 三大圓環進度條 */}
      <div className="grid grid-cols-3 gap-2.5">
        <ProgressRing
          label="剩餘熱量"
          value={s.remaining_calories}
          max={user.daily_calorie_target}
          unit="kcal"
          colorClass="text-emerald-500"
          subtext={`已吃 ${s.consumed_calories}`}
        />
        <ProgressRing
          label="剩餘蛋白質"
          value={s.remaining_protein_g}
          max={user.protein_g}
          unit="g"
          colorClass="text-sky-500"
          subtext={`目標 ${user.protein_g}g`}
        />
        <ProgressRing
          label="建議飲水"
          value={s.target_water_ml}
          max={s.target_water_ml}
          unit="ml"
          colorClass="text-cyan-500"
          subtext="隨運動動態調整"
        />
      </div>

      {/* 碳水與脂肪 */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-100 dark:border-slate-800 flex justify-between text-xs">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-amber-500" />
          <span>碳水：{s.consumed_carbs_g} / {s.target_carbs_g} g</span>
        </div>
        <div className="flex items-center gap-2">
          <Droplets className="w-4 h-4 text-purple-500" />
          <span>脂肪：{s.consumed_fat_g} / {user.fat_g} g</span>
        </div>
      </div>

      {/* 今日飲食紀錄 */}
      <div>
        <h3 className="font-bold text-sm mb-2.5 px-1">今日飲食紀錄 ({meals.length})</h3>
        {meals.length === 0 ? (
          <div className="text-center py-8 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-xs text-slate-400">
            今天還沒記錄喔！點擊下方中間相機按鈕 10 秒記一筆
          </div>
        ) : (
          <div className="space-y-2">
            {meals.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between bg-white dark:bg-slate-900 p-3.5 rounded-2xl border border-slate-100 dark:border-slate-800"
              >
                <div>
                  <p className="font-semibold text-sm">{m.food_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {m.calories} kcal • 蛋 {m.protein_g}g • 碳 {m.carbs_g}g • 脂 {m.fat_g}g
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(m.id)}
                  className="p-2 text-slate-400 hover:text-rose-500"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}