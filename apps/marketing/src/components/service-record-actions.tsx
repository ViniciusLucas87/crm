"use client";

import { useState } from "react";

export function ServiceRecordActions({ token }: { token: string }) {
  const [note, setNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  async function submit(actionType: "request_service" | "ask_question" | "stop_reminders") {
    setSending(true); setMessage(null);
    const api = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api.pacificnorthsystems.com";
    const response = await fetch(`${api}/api/v1/never-forget/public/${encodeURIComponent(token)}/actions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action_type: actionType, note: note || null }) });
    const payload = await response.json().catch(() => ({})); setSending(false);
    setMessage(response.ok ? payload.message : "Your request could not be sent. Please contact the contractor directly.");
  }
  return <div className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-bold">Need help with this work?</h2><textarea value={note} onChange={event => setNote(event.target.value)} placeholder="Add a short note for the contractor" rows={3} className="mt-4 w-full rounded-xl border border-slate-300 px-3 py-2" /><div className="mt-3 flex flex-wrap gap-2"><button disabled={sending} onClick={() => void submit("request_service")} className="rounded-xl bg-[#10c9df] px-4 py-2 font-bold text-[#071a2d]">Request another visit</button><button disabled={sending} onClick={() => void submit("ask_question")} className="rounded-xl border border-slate-300 px-4 py-2 font-semibold">Ask a question</button><button disabled={sending} onClick={() => void submit("stop_reminders")} className="px-3 py-2 text-sm text-slate-500 underline">Stop reminders</button></div>{message && <p className="mt-3 text-sm text-slate-600">{message}</p>}</div>;
}
