import { useState } from "react";
import { Camera, Type, Edit3, X, Loader2, Check } from "lucide-react";
import { api } from "../services/api";

export default function CameraLoggerModal({ userId, isOpen, onClose, onSaved }) {
  const [tab, setTab] = useState("photo"); // photo | text | manual
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [textInput, setTextInput] = useState("");
  const [hint, setHint] = useState("");

  const [form, setForm] = useState({
    food_name: "",
    portion_desc: "1 份",
    calories: "",
    protein_g: "",
    carbs_g: "",
    fat_g: "",
    meal_slot: "flexible",
    notes: "",
    ai_confidence: "",
  });

  if (!isOpen) return null;

  const handlePhotoChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.analyzePhoto(file, hint);
      setForm({
        ...form,
        food_name: res.food_name,
        portion_desc: res.estimated_portion,
        calories: res.calories,
        protein_g: res.protein_g,
        carbs_g: res.carbs_g,
        fat_g: res.fat_g,
        ai_confidence: res.confidence,
        notes: res.notes || "",
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleParseText = async () => {
    if (!textInput.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.parseFoodText(textInput);
      setForm({
        ...form,
        food_name: res.food_name,
        portion_desc: res.estimated_portion,
        calories: res.calories,
        protein_g: res.protein_g,
        carbs_g: res.carbs_g,
        fat_g: res.fat_g,
        ai_confidence: res.confidence,
        notes: res.notes || "",
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.food_name || form.calories === "") return;
    setLoading(true);
    setError("");
    try {
      await api.logMeal({
        user_id: userId,
        meal_slot: form.meal_slot,
        source_type: tab,
        raw_input: tab === "text" ? textInput : null,
        food_name: form.food_name,
        portion_desc: form.portion_desc || "1 份",
        calories: Number(form.calories),
        protein_g: Number(form.protein_g || 0),
        carbs_g: Number(form.carbs_g || 0),
        fat_g: Number(form.fat_g || 0),
        ai_confidence: form.ai_confidence || null,
        notes: form.notes || null,
      });
      onSaved();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-t-3xl sm:rounded-3xl p-5 max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">三軌飲食記錄</h3>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 切換三軌模式 */}
        <div className="grid grid-cols-3 gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl mb-4 text-xs font-medium">
          {[
            { id: "photo", label: "拍照辨識", icon: Camera },
            { id: "text", label: "AI 文字解析", icon: Type },
            { id: "manual", label: "手動輸入", icon: Edit3 },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setTab(item.id)}
                className={`flex items-center justify-center gap-1.5 py-2 rounded-xl transition ${
                  tab === item.id
                    ? "bg-white dark:bg-slate-900 text-emerald-600 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            );
          })}
        </div>

        {tab === "photo" && (
          <div className="space-y-3 mb-4">
            <input
              type="text"
              placeholder="選填補充說明（例如：飯只吃一半、無糖）"
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
            />
            <label className="flex flex-col items-center justify-center border-2 border-dashed border-emerald-400/70 rounded-2xl py-6 cursor-pointer bg-emerald-50/40 dark:bg-emerald-950/20 hover:bg-emerald-50 transition">
              <Camera className="w-8 h-8 text-emerald-500 mb-1.5" />
              <span className="text-sm font-semibold text-emerald-600">點擊拍照或從相簿上傳</span>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handlePhotoChange}
                className="hidden"
              />
            </label>
          </div>
        )}

        {tab === "text" && (
          <div className="space-y-2.5 mb-4">
            <textarea
              rows={2}
              placeholder="例如：超商無糖豆漿一瓶 + 茶葉蛋兩顆"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
            />
            <button
              type="button"
              onClick={handleParseText}
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-semibold flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "AI 自動估算營養素"}
            </button>
          </div>
        )}

        {error && <p className="text-xs text-rose-500 mb-3">{error}</p>}
        {loading && (
          <div className="flex items-center justify-center gap-2 text-sm text-emerald-600 py-3">
            <Loader2 className="w-4 h-4 animate-spin" />
            AI 營養師估算中...
          </div>
        )}

        {/* 確認與微調表單 */}
        <form onSubmit={handleSave} className="space-y-3">
          <div>
            <label className="text-xs text-slate-500">食物名稱</label>
            <input
              required
              value={form.food_name}
              onChange={(e) => setForm({ ...form, food_name: e.target.value })}
              placeholder="食物名稱"
              className="w-full mt-1 px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <div>
              <label className="text-xs text-slate-500">熱量 (kcal)</label>
              <input
                required
                type="number"
                value={form.calories}
                onChange={(e) => setForm({ ...form, calories: e.target.value })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500">蛋白質 (g)</label>
              <input
                type="number"
                step="0.1"
                value={form.protein_g}
                onChange={(e) => setForm({ ...form, protein_g: e.target.value })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500">碳水 (g)</label>
              <input
                type="number"
                step="0.1"
                value={form.carbs_g}
                onChange={(e) => setForm({ ...form, carbs_g: e.target.value })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500">脂肪 (g)</label>
              <input
                type="number"
                step="0.1"
                value={form.fat_g}
                onChange={(e) => setForm({ ...form, fat_g: e.target.value })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
              />
            </div>
          </div>

          {form.notes && (
            <p className="text-xs text-slate-500 bg-slate-50 dark:bg-slate-800 p-2.5 rounded-xl">
              💡 {form.notes}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-2xl bg-slate-900 dark:bg-emerald-500 text-white font-semibold flex items-center justify-center gap-2"
          >
            <Check className="w-4 h-4" />
            確認並一鍵記錄
          </button>
        </form>
      </div>
    </div>
  );
}