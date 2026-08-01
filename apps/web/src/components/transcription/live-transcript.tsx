"use client";

import { useEffect, useRef, useState } from "react";
import {
  Mic, Radio, AlertCircle, Copy, Download, Search, X,
  Activity, Wifi, WifiOff, VolumeX, CheckCircle2
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { TranscriptionState, TranscriptSegment, ChannelHealth } from "@/lib/transcription";

type Props = { state: TranscriptionState; onStop: () => void };

function HealthBadge({ label, health }: { label: string; health: ChannelHealth }) {
  const config: Record<ChannelHealth, { icon: React.ReactNode; cls: string; text: string }> = {
    waiting:   { icon: <Activity className="w-2.5 h-2.5" />, cls: "bg-gray-700 text-gray-400", text: "Waiting" },
    connecting:{ icon: <Activity className="w-2.5 h-2.5 animate-pulse" />, cls: "bg-amber-400/10 text-amber-400", text: "Connecting" },
    streaming: { icon: <Wifi className="w-2.5 h-2.5" />, cls: "bg-emerald-400/10 text-emerald-400", text: "Live" },
    silent:    { icon: <VolumeX className="w-2.5 h-2.5" />, cls: "bg-amber-400/10 text-amber-400", text: "Silent" },
    unavailable:{ icon: <WifiOff className="w-2.5 h-2.5" />, cls: "bg-gray-700 text-gray-500", text: "Unavail" },
    failed:    { icon: <AlertCircle className="w-2.5 h-2.5" />, cls: "bg-red-400/10 text-red-400", text: "Failed" },
    stopped:   { icon: <CheckCircle2 className="w-2.5 h-2.5" />, cls: "bg-gray-700 text-gray-500", text: "Stopped" },
  };
  const c = config[health] || config.waiting;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-medium ${c.cls}`}>
      {c.icon}{label}: {c.text}
    </span>
  );
}

export function LiveTranscript({ state, onStop }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.segments?.length ?? 0]);

  const filtered = searchTerm
    ? (state.segments || []).filter(s => s.text.toLowerCase().includes(searchTerm.toLowerCase()))
    : (state.segments || []);

  const handleExport = () => {
    const segs = state.segments || [];
    const text = segs.filter(s => s.isFinal)
      .map(s => `[${fmt(s.start)}] ${s.speaker}: ${s.text}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `transcript-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const handleCopy = () => {
    const segs = state.segments || [];
    const text = segs.filter(s => s.isFinal)
      .map(s => `[${fmt(s.start)}] ${s.speaker}: ${s.text}`).join("\n\n");
    navigator.clipboard.writeText(text);
  };

  return (
    <Card className="flex flex-col h-full bg-gray-900 border-gray-700">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Radio className={`w-4 h-4 ${state.isStreaming ? "text-emerald-400 animate-pulse" : "text-gray-500"}`} />
          <h3 className="text-sm font-semibold text-gray-200">Live Transcript</h3>
        </div>
        <div className="flex items-center gap-1.5">
          <HealthBadge label="Agent" health={state.agentHealth} />
          <HealthBadge label="Prospect" health={state.prospectHealth} />
        </div>
        <div className="flex items-center gap-1">
          {showSearch ? (
            <div className="flex items-center gap-1">
              <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                placeholder="Search..." className="w-40 px-2 py-1 text-xs rounded bg-gray-800 border border-gray-600 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-400/50" />
              <Button variant="ghost" size="sm" onClick={() => { setShowSearch(false); setSearchTerm(""); }} className="p-1 h-auto"><X className="w-3.5 h-3.5" /></Button>
            </div>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => setShowSearch(true)} className="p-1.5 h-auto"><Search className="w-3.5 h-3.5 text-gray-400" /></Button>
              <Button variant="ghost" size="sm" onClick={handleCopy} className="p-1.5 h-auto"><Copy className="w-3.5 h-3.5 text-gray-400" /></Button>
              <Button variant="ghost" size="sm" onClick={handleExport} className="p-1.5 h-auto"><Download className="w-3.5 h-3.5 text-gray-400" /></Button>
            </>
          )}
        </div>
      </div>

      <div className="px-4 py-2 border-b border-gray-700 flex items-center gap-3">
        {state.isStreaming ? (
          <Button onClick={onStop} className="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white text-xs px-3 py-1.5 rounded-lg"><X className="w-3.5 h-3.5" />Stop</Button>
        ) : state.isConnected ? (
          <div className="flex items-center gap-2 text-emerald-400 text-xs"><Radio className="w-3.5 h-3.5 animate-pulse" />Streaming…</div>
        ) : (
          <div className="flex items-center gap-2 text-amber-400 text-xs"><Radio className="w-3.5 h-3.5" />Initializing…</div>
        )}
        {state.error && <div className="flex items-center gap-1 text-red-400 text-xs"><AlertCircle className="w-3 h-3" />{state.error}</div>}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1.5 min-h-[200px] max-h-[500px]">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-sm gap-2">
            <Mic className="w-8 h-8 opacity-30" />
            {state.isStreaming ? "Listening…" : "Transcription starts automatically when the call connects"}
          </div>
        )}
        {filtered.map(seg => (
          <Bubble key={seg.id} segment={seg} isSearchResult={!!searchTerm} />
        ))}
      </div>

      {state.isStreaming && (
        <div className="px-4 py-2 border-t border-gray-700 text-[10px] text-gray-500 flex justify-between">
          <span>{(state.segments || []).filter(s => s.isFinal).length} utterances</span>
          <span>{state.fullText.split(/\s+/).filter(Boolean).length} words</span>
        </div>
      )}

      {/* ── PART 14: Diagnostics Panel (collapsible) ── */}
      <DiagnosticsPanel state={state} />
    </Card>
  );
}

function DiagnosticsPanel({ state }: { state: TranscriptionState }) {
  const [open, setOpen] = useState(false);
  if (!state.isStreaming && state.agentHealth === "waiting" && state.prospectHealth === "waiting") return null;

  const diagBlock = (label: string, diag: typeof state.agentDiagnostics) => {
    if (!diag) return <div className="text-[10px] text-gray-600">No data</div>;
    return (
      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px] font-mono">
        <span className="text-gray-500">track:</span><span className="text-gray-300 truncate">{diag.trackId.slice(0, 12)}</span>
        <span className="text-gray-500">state:</span><span className={diag.trackState === "live" ? "text-emerald-400" : "text-red-400"}>{diag.trackState}</span>
        <span className="text-gray-500">in rate:</span><span>{diag.inputSampleRate}Hz</span>
        <span className="text-gray-500">out rate:</span><span>{diag.outputSampleRate}Hz</span>
        <span className="text-gray-500">RMS:</span><span>{diag.rmsLevel.toFixed(4)}</span>
        <span className="text-gray-500">peak:</span><span>{diag.peakLevel.toFixed(3)}</span>
        <span className="text-gray-500">chunks:</span><span>{diag.chunksSent}</span>
        <span className="text-gray-500">bytes:</span><span>{(diag.bytesSent / 1024).toFixed(1)}KB</span>
        <span className="text-gray-500">silent:</span><span className={diag.silent ? "text-amber-400" : "text-emerald-400"}>{diag.silent ? "YES" : "no"}</span>
        <span className="text-gray-500">active:</span><span>{diag.activeChunks}</span>
        <span className="text-gray-500">silent#:</span><span>{diag.silentChunks}</span>
        <span className="text-gray-500">zero%:</span><span>{diag.zeroSamplePct.toFixed(1)}</span>
        <span className="text-gray-500">clip%:</span><span className={diag.clippingPct > 1 ? "text-red-400" : ""}>{diag.clippingPct.toFixed(1)}</span>
      </div>
    );
  };

  return (
    <div className="border-t border-gray-700">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-1.5 flex items-center justify-between text-[10px] text-gray-500 hover:text-gray-300 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <Activity className="w-3 h-3" />
          Pipeline Diagnostics
        </span>
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-4 pb-3 space-y-2">
          <div>
            <div className="text-[10px] font-semibold text-gray-400 mb-1 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" /> Agent Audio
            </div>
            {diagBlock("Agent", state.agentDiagnostics)}
          </div>
          <div>
            <div className="text-[10px] font-semibold text-gray-400 mb-1 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-purple-400 inline-block" /> Prospect Audio
            </div>
            {diagBlock("Prospect", state.prospectDiagnostics)}
          </div>
          <div>
            <div className="text-[10px] font-semibold text-gray-400 mb-1 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> AI Coach
            </div>
            <div className="text-[10px] text-gray-500">
              finals: agent={(state.segments || []).filter(s => s.sourceRole === "agent" && s.isFinal).length} prospect={(state.segments || []).filter(s => s.sourceRole === "prospect" && s.isFinal).length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Bubble({ segment, isSearchResult }: { segment: TranscriptSegment; isSearchResult: boolean }) {
  const isAgent = segment.speaker === "PNS Agent";
  const label = segment.speaker || "Unknown";
  const opacity = segment.isFinal ? "opacity-100" : "opacity-60";

  return (
    <div className={`flex ${isAgent ? "justify-start" : "justify-end"} ${opacity}`}>
      <div className={`max-w-[80%] rounded-lg px-2.5 py-1.5 ${isAgent
          ? "bg-gray-800 text-gray-200 rounded-tl-sm"
          : isSearchResult ? "bg-amber-900/60 text-amber-100 rounded-tr-sm"
          : "bg-emerald-900/40 text-emerald-100 rounded-tr-sm"}`}>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-semibold text-gray-400">{label}</span>
          <span className="text-[9px] text-gray-500">{fmt(segment.start)}</span>
          {!segment.isFinal && <span className="text-[10px] text-amber-400 animate-pulse">•••</span>}
        </div>
        <p className="text-[13px] leading-snug mt-0.5">{segment.text}</p>
      </div>
    </div>
  );
}

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
