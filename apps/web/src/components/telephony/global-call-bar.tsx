"use client";

import { useTelephony } from "@/lib/telephony-context";
import { PhoneOff, Mic, MicOff, Pause, Play, Circle, ChevronDown, Radio } from "lucide-react";

function formatDuration(s: number) {
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  const mins = m % 60;
  const sec = s % 60;
  if (h > 0) return `${h}:${mins.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export function GlobalCallBar() {
  const { call, endCall, toggleMute, toggleHold, toggleRecording, resetCall, setMinimized, isMinimized } = useTelephony();
  const isActive = ["dialing", "ringing", "connected", "muted", "on_hold", "recording"].includes(call.state);

  if (call.state === "idle" || call.state === "registering") return null;

  // ── Ended / Failed ──
  if (call.state === "ended" || call.state === "failed") {
    return (
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-slate-900/95 backdrop-blur-xl">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-red-500/20 p-2">
              <PhoneOff className="h-4 w-4 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">
                {call.state === "failed" ? "Call failed" : "Call ended"}
              </p>
              {call.duration > 0 && <p className="text-xs text-slate-400">{formatDuration(call.duration)}</p>}
              {call.error && <p className="text-xs text-red-400">{call.error}</p>}
            </div>
          </div>
          <button onClick={resetCall} className="rounded-lg bg-white/10 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/20">
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  const label = call.companyName || call.contactName || call.phoneNumber;
  const sublabel = call.state === "dialing" ? "Dialing…"
    : call.state === "ringing" ? "Ringing…"
    : call.state === "on_hold" ? "On Hold"
    : formatDuration(call.duration);

  // ── Minimized ──
  if (isMinimized) {
    return (
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-slate-900/95 backdrop-blur-xl">
        <div className="flex items-center justify-between px-4 py-2">
          <button onClick={() => setMinimized(false)} className="flex items-center gap-3 text-left hover:opacity-80">
            <div className={`h-2.5 w-2.5 rounded-full animate-pulse ${
              call.state === "recording" ? "bg-red-400" : call.state === "on_hold" ? "bg-amber-400" : "bg-emerald-400"
            }`} />
            <div>
              <p className="text-sm font-medium text-white">{label}</p>
              <p className="text-xs text-slate-400">{sublabel}</p>
            </div>
          </button>
          <button onClick={() => setMinimized(false)} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white">
            <ChevronDown className="h-4 w-4 rotate-180" />
          </button>
        </div>
      </div>
    );
  }

  // ── Full call bar ──
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 bg-slate-900/95 backdrop-blur-xl shadow-2xl shadow-black/40">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className={`h-2.5 w-2.5 rounded-full animate-pulse shrink-0 ${
            call.state === "recording" ? "bg-red-400" : call.state === "on_hold" ? "bg-amber-400" :
            call.state === "muted" ? "bg-yellow-400" : call.state === "ringing" ? "bg-blue-400" : "bg-emerald-400"
          }`} />
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pacific North Systems</p>
            <p className="text-sm font-medium text-white truncate">{label}</p>
            <div className="flex items-center gap-2">
              <p className="text-xs text-slate-400">{sublabel}</p>
              {call.phoneNumber && (
                <p className="text-xs text-slate-500">{call.phoneNumber}</p>
              )}
              {call.recording && (
                <span className="flex items-center gap-1 text-xs text-red-400">
                  <Circle className="h-2 w-2 fill-red-400" /> REC
                </span>
              )}
              {isActive && !call.held && call.state !== "on_hold" && (
                <span className="flex items-center gap-1 text-xs text-slate-500"><Radio className="h-2.5 w-2.5" /></span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button onClick={toggleMute} className={`rounded-lg p-2 transition ${
            call.muted ? "bg-red-500/20 text-red-400" : "text-slate-400 hover:bg-white/10 hover:text-white"
          }`} title={call.muted ? "Unmute" : "Mute"}>
            {call.muted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
          <button onClick={toggleHold} className={`rounded-lg p-2 transition ${
            call.held ? "bg-amber-500/20 text-amber-400" : "text-slate-400 hover:bg-white/10 hover:text-white"
          }`} title={call.held ? "Resume" : "Hold"}>
            {call.held ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
          </button>
          <button onClick={toggleRecording} className={`rounded-lg p-2 transition ${
            call.recording ? "bg-red-500/20 text-red-400" : "text-slate-400 hover:bg-white/10 hover:text-white"
          }`} title={call.recording ? "Stop Recording" : "Record"}>
            <Circle className={`h-4 w-4 ${call.recording ? "fill-red-400" : ""}`} />
          </button>
          <button onClick={endCall} className="ml-2 rounded-full bg-red-500 p-2.5 text-white hover:bg-red-600 transition" title="End Call">
            <PhoneOff className="h-4 w-4" />
          </button>
          <button onClick={() => setMinimized(true)} className="ml-1 rounded-lg p-2 text-slate-500 hover:bg-white/10 hover:text-slate-300 transition" title="Minimize">
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
