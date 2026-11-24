import { useEffect, useState } from "react";
import { Send, ImagePlus, X, Bot, Loader2 } from "lucide-react";
import { api } from "../services/api";

export default function AiChatDrawer({ userId, isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && userId) {
      api.getChatHistory(userId).then((res) => setMessages(res.messages || [])).catch(() => {});
    }
  }, [isOpen, userId]);

  if (!isOpen) return null;

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() && !imageFile) return;

    const userText = input.trim() || "幫我看看這張照片怎麼吃比較好？";
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInput("");
    const fileToSend = imageFile;
    setImageFile(null);
    setLoading(true);

    try {
      const res = await api.sendChat(userId, userText, fileToSend);
      setMessages((prev) => [...prev, { role: "model", content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "model", content: `發生錯誤：${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md h-[82vh] bg-white dark:bg-slate-900 rounded-t-3xl flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm">FlexFit AI 飲控小助手</h3>
              <p className="text-[11px] text-slate-400">知道你今天的剩餘額度，隨時問怎麼吃</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center text-xs text-slate-400 mt-8 space-y-2">
              <p>試著問我：</p>
              <p className="bg-slate-100 dark:bg-slate-800 inline-block px-3 py-1.5 rounded-xl">
                「我現在外面只有麥當勞跟 7-11，剩餘額度怎麼吃？」
              </p>
            </div>
          )}
          {messages.map((m, idx) => (
            <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
                  m.role === "user"
                    ? "bg-emerald-500 text-white rounded-br-sm"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-sm"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              小助手思考中...
            </div>
          )}
        </div>

        <form onSubmit={handleSend} className="p-3 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
          <label className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 cursor-pointer">
            <ImagePlus className="w-5 h-5" />
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(e) => setImageFile(e.target.files?.[0] || null)}
              className="hidden"
            />
          </label>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={imageFile ? `已選照片 (${imageFile.name})，輸入問題...` : "輸入問題或傳菜單照片..."}
            className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-sm outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="p-2.5 rounded-xl bg-emerald-500 text-white"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}