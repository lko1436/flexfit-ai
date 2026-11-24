import { useState } from "react";
import { ArrowRight, CheckCircle2, Sparkles } from "lucide-react";
import { api } from "../services/api";
import GuardrailModal from "../components/GuardrailModal";

export default function OnboardingPage({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(null);
  const [goalOptions, setGoalOptions] = useState([]);
  const [guardrail, setGuardrail] = useState(null);

  const [profile, setProfile] = useState({
    nickname: "飲控夥伴",
    height_cm: "",
    weight_kg: "",
    gender: "unspecified",
    age: "",
    activity_level: "light",
  });

  const [goalMode, setGoalMode] = useState("suggested");
  const [selectedTier, setSelectedTier] = useState("standard");
  const [customTargetWeight, setCustomTargetWeight] = useState("");
  const [customWeeks, setCustomWeeks] = useState("");

  const handleStep1 = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.onboard({
        nickname: profile.nickname || "飲控夥伴",
        height_cm: Number(profile.height_cm),
        weight_kg: Number(profile.weight_kg),
        gender: profile.gender,
        age: profile.age ? Number(profile.age) : null,
        activity_level: profile.activity_level,
      });
      setUserId(res.user.id);
      setGoalOptions(res.suggested_goals);
      setStep(2);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitGoal = async (override = false, overrideWeeks = null) => {
    setLoading(true);
    try {
      const payload =
        goalMode === "suggested"
          ? { mode: "suggested", tier: selectedTier }
          : {
              mode: "custom",
              target_weight_kg: Number(customTargetWeight),
              target_weeks: overrideWeeks || Number(customWeeks),
              force_override: override,
            };
      const res = await api.setGoal(userId, payload);
      if (!res.applied) {
        setGuardrail(res.guardrail);
        return;
      }
      setGuardrail(null);
      onComplete(userId);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto min-h-screen px-5 py-8 flex flex-col justify-center">
      <div className="mb-6">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
          <Sparkles className="w-3.5 h-3.5" /> FlexFit AI
        </span>
        <h1 className="text-2xl font-bold mt-3">
          {step === 1 ? "30 秒極簡開始" : "選擇你的減脂節奏"}
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          {step === 1 ? "不問體脂率與 InBody，只要身高體重就能開始。" : "可選系統建議體位，或自訂目標（內建健康防呆）。"}
        </p>
      </div>

      {step === 1 ? (
        <form onSubmit={handleStep1} className="space-y-4 bg-white dark:bg-slate-900 p-5 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-800">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-500">目前身高 (cm) *</label>
              <input
                required
                type="number"
                step="0.1"
                placeholder="168"
                value={profile.height_cm}
                onChange={(e) => setProfile({ ...profile, height_cm: e.target.value })}
                className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500">目前體重 (kg) *</label>
              <input
                required
                type="number"
                step="0.1"
                placeholder="70"
                value={profile.weight_kg}
                onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value })}
                className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
            <div>
              <label className="text-xs text-slate-400">性別（選填）</label>
              <select
                value={profile.gender}
                onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                className="w-full mt-1 px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm"
              >
                <option value="unspecified">略過（預設估算）</option>
                <option value="female">女性</option>
                <option value="male">男性</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400">年齡（選填）</label>
              <input
                type="number"
                placeholder="選填"
                value={profile.age}
                onChange={(e) => setProfile({ ...profile, age: e.target.value })}
                className="w-full mt-1 px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold flex items-center justify-center gap-2"
          >
            下一步：計算專屬目標 <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl text-xs font-semibold">
            <button
              onClick={() => setGoalMode("suggested")}
              className={`py-2.5 rounded-xl ${goalMode === "suggested" ? "bg-white dark:bg-slate-900 shadow-sm text-emerald-600" : "text-slate-500"}`}
            >
              系統建議體位 (3 選 1)
            </button>
            <button
              onClick={() => setGoalMode("custom")}
              className={`py-2.5 rounded-xl ${goalMode === "custom" ? "bg-white dark:bg-slate-900 shadow-sm text-emerald-600" : "text-slate-500"}`}
            >
              自訂目標體重/週數
            </button>
          </div>

          {goalMode === "suggested" ? (
            <div className="space-y-2.5">
              {goalOptions.map((opt) => (
                <button
                  key={opt.tier}
                  onClick={() => setSelectedTier(opt.tier)}
                  className={`w-full text-left p-4 rounded-2xl border transition ${
                    selectedTier === opt.tier
                      ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30"
                      : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold">{opt.title}</span>
                    {selectedTier === opt.tier && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{opt.subtitle}</p>
                  <div className="mt-2 flex gap-3 text-xs font-medium text-emerald-600">
                    <span>目標 {opt.target_weight_kg} kg ({opt.target_weeks} 週)</span>
                    <span>•</span>
                    <span>每日 {opt.daily_calorie_target} kcal</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 p-5 rounded-3xl border border-slate-100 dark:border-slate-800 space-y-3">
              <div>
                <label className="text-xs text-slate-500">目標體重 (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="例如：62"
                  value={customTargetWeight}
                  onChange={(e) => setCustomTargetWeight(e.target.value)}
                  className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500">預計達成週數</label>
                <input
                  type="number"
                  placeholder="例如：12"
                  value={customWeeks}
                  onChange={(e) => setCustomWeeks(e.target.value)}
                  className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800"
                />
              </div>
            </div>
          )}

          <button
            onClick={() => submitGoal(false)}
            disabled={loading}
            className="w-full py-3.5 rounded-2xl bg-emerald-500 text-white font-semibold shadow-lg shadow-emerald-500/20"
          >
            開始我的靈活飲控
          </button>
        </div>
      )}

      <GuardrailModal
        guardrail={guardrail}
        onApplyRecommended={(recWeeks) => {
          setCustomWeeks(String(recWeeks));
          submitGoal(false, recWeeks);
        }}
        onForceOverride={() => submitGoal(true)}
        onClose={() => setGuardrail(null)}
      />
    </div>
  );
}