export default function ProgressRing({
  label,
  value,
  max,
  unit,
  colorClass = "text-emerald-500",
  subtext = "",
}) {
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const pct = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  const offset = circumference * (1 - pct);

  return (
    <div className="flex flex-col items-center bg-white dark:bg-slate-900 rounded-2xl p-3 shadow-sm border border-slate-100 dark:border-slate-800">
      <div className="relative w-24 h-24 flex items-center justify-center">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
          <circle
            cx="48"
            cy="48"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-slate-100 dark:text-slate-800"
          />
          <circle
            cx="48"
            cy="48"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={`${colorClass} transition-all duration-500`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-lg font-bold leading-tight">{Math.round(value)}</span>
          <span className="text-[11px] text-slate-400">{unit}</span>
        </div>
      </div>
      <span className="mt-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200">{label}</span>
      {subtext && <span className="text-[11px] text-slate-400 mt-0.5">{subtext}</span>}
    </div>
  );
}