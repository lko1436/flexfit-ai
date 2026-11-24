const BASE_URL = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "請求失敗，請稍後再試");
  }
  return data;
}

export const api = {
  // User & Onboarding
  onboard: (payload) =>
    request("/api/user/onboarding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getGoalOptions: (userId) => request(`/api/user/${userId}/goal-options`),

  setGoal: (userId, payload) =>
    request(`/api/user/${userId}/goal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getDashboard: (userId) => request(`/api/user/${userId}/dashboard`),

  // Meals & AI Vision
  analyzePhoto: (file, userHint = "") => {
    const form = new FormData();
    form.append("file", file);
    if (userHint) form.append("user_hint", userHint);
    return request("/api/meals/analyze-photo", { method: "POST", body: form });
  },

  parseFoodText: (text) =>
    request("/api/meals/parse-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }),

  logMeal: (payload) =>
    request("/api/meals/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  deleteMeal: (logId) => request(`/api/meals/${logId}`, { method: "DELETE" }),

  // Schedule, Eating Out & Chat
  saveSchedule: (payload) =>
    request("/api/recommend/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getTodaySchedule: (userId) => request(`/api/recommend/schedule/${userId}/today`),

  recommendEatingOut: (payload) =>
    request("/api/recommend/eating-out", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  saveCustomFood: (payload) =>
    request("/api/recommend/foods", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  sendChat: (userId, message, imageFile = null) => {
    const form = new FormData();
    form.append("user_id", String(userId));
    form.append("message", message);
    if (imageFile) form.append("image", imageFile);
    return request("/api/recommend/chat", { method: "POST", body: form });
  },

  getChatHistory: (userId) => request(`/api/recommend/chat/${userId}/history`),
};