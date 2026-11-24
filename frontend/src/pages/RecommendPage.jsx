import { useState } from "react";
import { Sparkles, Loader2, BookmarkPlus } from "lucide-react";
import { api } from "../services/api";

const SCENES = [
  { id: "convenience_store", label: "🏪 7-11 / 全家" },
  { id: "breakfast_shop", label: "🥪 傳統早餐店" },
  { id: "bento_buffet", label: "🍱 自助餐 / 便當" },
  { id: "luwei_salty_chicken", label: "🥗 滷味 / 鹹水雞" },
  { id: "fast_food", label: "🍔 速食店" },
  { id: "beverage_sugar_free", label: "🧋 手搖飲無糖替代" },
];

export default function RecommendPage({ userId }) {
  const [scene, setScene] = useState("convenience_store");
  const [pref, setPref] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRecommend = async () => {
    setLoading(true);
    try {
      const res = await api.recommendEatingOut({
        user_id: userId,
        scene_tag: scene,
        user_preference: pref || null,
      });
      setResult(res);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveComboToLibrary = async (combo) => {
    await api.saveCustomFood({
      name: combo.combo_title,
      scene_tag: scene,
      store_brand: "我的常吃組合",
      portion_desc: combo.items.join(" + "),
      calories: combo.total_calories,
      protein_g: combo.protein_g,
      carbs_g: combo.carbs_g,
      fat_g: combo.fat_g,
      tags: ["AI推薦收藏"],
    });
    alert("已動態收藏到您的個人食物資料庫！");
  };

  return (
    <div className="space-y-4 pb-24">
      <div className="bg-white dark:bg-slate-900 rounded-3xl p-5 border border-slate-100 dark:border-slate-800 space-y-4">
        <div>
          <h2 className="font-bold text-base">靈活外食 AI 組合器</h2>
          <p className="text-xs text-slate-400 mt-0.5">不寫死菜單，依你現在剩餘的扣打即時配餐</p>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {SCENES.map((s) => (
            <button
              key={s.id}
              onClick={() => setScene(s.id)}
              className={`py-2.5 px-3 rounded-xl text-xs font-medium text-left border transition ${
                scene === s.id
                  ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600"
                  : "border-slate-200 dark:border-slate-800"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <input
          value={pref}
          onChange={(e) => setPref(e.target.value)}
          placeholder="選填需求（例如：預算150元內、想喝熱湯）"
          className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 text-sm"
        />

        <button
          onClick={handleRecommend}
          disabled={loading}
          className="w-full py-3 rounded-2xl bg-emerald-500 text-white font-semibold text-sm flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          依剩餘額度即時推薦
        </button>
      </div>

      {result && (
        <div className="space-y-3">
          <p className="text-xs text-slate-500 px-1">
            目前剩餘：<b>{result.remaining_calories} kcal</b> • 蛋白質 <b>{result.remaining_protein_g}g</b>
          </p>
          {result.combos.map((c, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-2">
              <div className="flex justify-between items-start gap-2">
                <h3 className="font-bold text-sm">{c.combo_title}</h3>
                <button
                  onClick={() => handleSaveComboToLibrary(c)}
                  className="text-xs text-emerald-600 flex items-center gap-1 shrink-0"
                >
                  <BookmarkPlus className="w-4 h-4" /> 收藏
                </button>
              </div>
              <ul className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                {c.items.map((item, i) => (
                  <li key={i}>• {item}</li>
                ))}
              </ul>
              <div className="text-xs font-semibold text-emerald-600">
                合計 {c.total_calories} kcal（蛋 {c.protein_g}g / 碳 {c.carbs_g}g / 脂 {c.fat_g}g）
              </div>
              <p className="text-xs text-slate-400">{c.why_it_fits}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}