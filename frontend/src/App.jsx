import { useCallback, useEffect, useState } from "react";
import { Moon, Sun, RotateCcw } from "lucide-react";
import { api } from "./services/api";
import OnboardingPage from "./pages/OnboardingPage";
import DashboardPage from "./pages/DashboardPage";
import SchedulePage from "./pages/SchedulePage";
import RecommendPage from "./pages/RecommendPage";
import BottomNav from "./components/BottomNav";
import CameraLoggerModal from "./components/CameraLoggerModal";
import AiChatDrawer from "./components/AiChatDrawer";

export default function App() {
  const [userId, setUserId] = useState(() => {
    const saved = localStorage.getItem("flexfit_user_id");
    return saved ? Number(saved) : null;
  });
  const [dark, setDark] = useState(false);
  const [activePage, setActivePage] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  const loadDashboard = useCallback(async () => {
    if (!userId) return;
    try {
      const res = await api.getDashboard(userId);
      setDashboard(res);
    } catch {
      localStorage.removeItem("flexfit_user_id");
      setUserId(null);
    }
  }, [userId]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleOnboardComplete = (newId) => {
    localStorage.setItem("flexfit_user_id", String(newId));
    setUserId(newId);
  };

  if (!userId) {
    return <OnboardingPage onComplete={handleOnboardComplete} />;
  }

  return (
    <div className="max-w-md mx-auto min-h-screen px-4 pt-4">
      <header className="flex items-center justify-between mb-4">
        <div>
          <h1 className="font-bold text-lg">FlexFit AI</h1>
          <p className="text-[11px] text-slate-400">
            Hi {dashboard?.user?.nickname || "夥伴"} • BMI {dashboard?.user?.bmi || "-"}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setDark((d) => !d)}
            className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800"
            aria-label="切換深淺色"
          >
            {dark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>
          <button
            onClick={() => {
              localStorage.removeItem("flexfit_user_id");
              setUserId(null);
            }}
            className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-400"
            title="重設資料"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </header>

      {activePage === "dashboard" && <DashboardPage data={dashboard} onRefresh={loadDashboard} />}
      {activePage === "schedule" && <SchedulePage userId={userId} onUpdated={loadDashboard} />}
      {activePage === "recommend" && <RecommendPage userId={userId} />}

      <BottomNav
        activePage={activePage}
        onNavigate={setActivePage}
        onOpenCamera={() => setCameraOpen(true)}
        onOpenChat={() => setChatOpen(true)}
      />

      <CameraLoggerModal
        userId={userId}
        isOpen={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onSaved={loadDashboard}
      />

      <AiChatDrawer
        userId={userId}
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
      />
    </div>
  );
}