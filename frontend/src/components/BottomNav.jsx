import { Home, CalendarClock, Camera, Utensils, MessageCircleHeart } from "lucide-react";

export default function BottomNav({ activePage, onNavigate, onOpenCamera, onOpenChat }) {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-t border-slate-200 dark:border-slate-800">
      <div className="max-w-md mx-auto flex items-center justify-around h-16 px-2">
        <button
          onClick={() => onNavigate("dashboard")}
          className={`flex flex-col items-center gap-0.5 text-[11px] ${
            activePage === "dashboard" ? "text-emerald-500 font-semibold" : "text-slate-400"
          }`}
        >
          <Home className="w-5 h-5" />
          首頁
        </button>

        <button
          onClick={() => onNavigate("schedule")}
          className={`flex flex-col items-center gap-0.5 text-[11px] ${
            activePage === "schedule" ? "text-emerald-500 font-semibold" : "text-slate-400"
          }`}
        >
          <CalendarClock className="w-5 h-5" />
          作息排程
        </button>

        <button
          onClick={onOpenCamera}
          className="-mt-6 w-14 h-14 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/30 flex items-center justify-center transition active:scale-95"
          aria-label="拍照記錄"
        >
          <Camera className="w-6 h-6" />
        </button>

        <button
          onClick={() => onNavigate("recommend")}
          className={`flex flex-col items-center gap-0.5 text-[11px] ${
            activePage === "recommend" ? "text-emerald-500 font-semibold" : "text-slate-400"
          }`}
        >
          <Utensils className="w-5 h-5" />
          外食推薦
        </button>

        <button
          onClick={onOpenChat}
          className="flex flex-col items-center gap-0.5 text-[11px] text-slate-400 hover:text-emerald-500"
        >
          <MessageCircleHeart className="w-5 h-5" />
          AI 助手
        </button>
      </div>
    </nav>
  );
}