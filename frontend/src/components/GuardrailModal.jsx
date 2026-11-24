import { AlertTriangle, Sparkles } from "lucide-react";

export default function GuardrailModal({ guardrail, onApplyRecommended, onForceOverride, onClose }) {
  if (!guardrail) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl border border-amber-200 dark:border-amber-900/50">
        <div className="flex items-center gap-3 text-amber-500 mb-3">
          <div className="p-2.5 rounded-2xl bg-amber-50 dark:bg-amber-950/50">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">健康減重防呆提醒</h3>
            <p className="text-xs text-slate-500">為了保護您的肌肉量與基礎代謝</p>
          </div>
        </div>

        <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 rounded-2xl p-4 mb-4">
          {guardrail.warnings?.map((w, idx) => (
            <p key={idx} className="leading-relaxed">• {w}</p>
          ))}
        </div>

        {guardrail.one_click_message && (
          <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl p-3.5 mb-5 text-sm text-emerald-800 dark:text-emerald-200 flex items-start gap-2">
            <Sparkles className="w-4 h-4 mt-0.5 shrink-0 text-emerald-500" />
            <span>{guardrail.one_click_message}</span>
          </div>
        )}

        <div className="flex flex-col gap-2.5">
          {guardrail.recommended_weeks && (
            <button
              onClick={() => onApplyRecommended(guardrail.recommended_weeks)}
              className="w-full py-3.5 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold shadow-md shadow-emerald-500/20 transition"
            >
              一鍵套用健康建議（調整為 {guardrail.recommended_weeks} 週）
            </button>
          )}
          <button
            onClick={onForceOverride}
            className="w-full py-2.5 rounded-2xl text-xs font-medium text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            我了解風險，仍維持目前設定
          </button>
          <button
            onClick={onClose}
            className="w-full py-2 text-xs text-slate-400"
          >
            返回修改數字
          </button>
        </div>
      </div>
    </div>
  );
}