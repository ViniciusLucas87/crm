"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle, Lightbulb, ThumbsUp, Activity,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import type { TranscriptSegment } from "@/lib/transcription";

type CoachEvent = {
  type: string;
  event_type: string;
  severity: "info" | "warning" | "critical" | "success";
  title: string;
  description: string;
  suggestion: string;
  evidence: string;
  confidence: number;
  timestamp: string;
  metadata?: Record<string, unknown>;
};

type ConversationHealth = {
  talk_ratio: number;
  engagement_score: number;
  rapport_score: number;
  overall_health: string;
  objections_handled: number;
  positive_signals: number;
};

type Props = {
  callId: string | number | null;
  isCallActive: boolean;
  segments: TranscriptSegment[];
  expanded?: boolean;
};

export function CoachPanel({ callId, isCallActive, segments, expanded = false }: Props) {
  const [events, setEvents] = useState<CoachEvent[]>([]);
  const [health, setHealth] = useState<ConversationHealth | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sentRef = useRef<Set<string>>(new Set());

  // Connect to coach WebSocket
  useEffect(() => {
    if (!callId || !isCallActive) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const apiHost = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/^https?:\/\//, "");
    const ws = new WebSocket(`${protocol}//${apiHost}/api/v1/sales-coach/coach/ws/${callId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "coach_event") {
          setEvents(prev => [...prev, data].slice(-50));
        } else if (data.type === "health") {
          setHealth(data);
        }
      } catch { /* ignore */ }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [callId, isCallActive]);

  // Forward new transcript segments to coach WebSocket
  useEffect(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    for (const seg of segments) {
      if (!sentRef.current.has(seg.id) && seg.isFinal) {
        sentRef.current.add(seg.id);
        wsRef.current.send(JSON.stringify({
          type: "segment",
          speaker: seg.speaker,
          text: seg.text,
          start: seg.start,
          end: seg.end,
          is_final: seg.isFinal,
          confidence: seg.confidence,
        }));
      }
    }
  }, [segments]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events.length]);

  if (!callId || !isCallActive) return null;

  const severityIcon = {
    info: <Lightbulb className="w-3.5 h-3.5 text-blue-400" />,
    warning: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />,
    critical: <AlertTriangle className="w-3.5 h-3.5 text-red-400" />,
    success: <ThumbsUp className="w-3.5 h-3.5 text-emerald-400" />,
  };

  const severityBg = {
    info: "bg-blue-400/10 border-blue-400/30",
    warning: "bg-amber-400/10 border-amber-400/30",
    critical: "bg-red-400/10 border-red-400/30",
    success: "bg-emerald-400/10 border-emerald-400/30",
  };

  return (
    <Card className={`flex flex-col bg-gray-900 border-gray-700 ${expanded ? "h-[min(72vh,760px)] min-h-[560px]" : "h-full"}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Activity className={`w-4 h-4 ${connected ? "text-emerald-400 animate-pulse" : "text-gray-500"}`} />
          <h3 className="text-sm font-semibold text-gray-200">AI Sales Coach</h3>
          {connected && <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-400/10 text-emerald-400">LIVE</span>}
        </div>
      </div>

      {/* Health bar */}
      {health && (
        <div className="px-4 py-2 border-b border-gray-700 space-y-2">
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>Conversation Health</span>
            <span className={health.overall_health === "good" ? "text-emerald-400" : health.overall_health === "at_risk" ? "text-red-400" : "text-amber-400"}>
              {health.overall_health.replace("_", " ").toUpperCase()}
            </span>
          </div>
          <div className="flex gap-2">
            <HealthMeter label="Engagement" value={health.engagement_score} />
            <HealthMeter label="Rapport" value={health.rapport_score} />
            <HealthMeter label="Talk Ratio" value={Math.round((1 - health.talk_ratio) * 100)} />
          </div>
          <div className="flex gap-3 text-[10px] text-gray-500">
            <span>🛑 {health.objections_handled} objections</span>
            <span>✅ {health.positive_signals} signals</span>
          </div>
        </div>
      )}

      {/* Events */}
      <div ref={scrollRef} className={`flex-1 overflow-y-auto p-3 space-y-2 min-h-[200px] ${expanded ? "max-h-none" : "max-h-[400px]"}`}>
        {events.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-xs gap-2">
            <Lightbulb className="w-6 h-6 opacity-30" />
            Waiting for conversation...
          </div>
        )}

        {events.map((evt, i) => (
          <div key={i} className={`rounded-lg border p-2.5 ${severityBg[evt.severity] || "bg-gray-800 border-gray-700"}`}>
            <div className="flex items-start gap-2">
              {severityIcon[evt.severity] || severityIcon.info}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-200">{evt.title}</span>
                  <span className="text-[9px] text-gray-500">{evt.confidence}%</span>
                </div>
                <p className="text-xs text-gray-300 mt-0.5">{evt.description}</p>
                {evt.suggestion && (
                  <p className="text-[11px] text-emerald-400 mt-1 italic">💡 {evt.suggestion}</p>
                )}
                {evt.evidence && (
                  <p className="text-[10px] text-gray-500 mt-1 truncate">📝 &ldquo;{evt.evidence.slice(0, 100)}&rdquo;</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function HealthMeter({ label, value }: { label: string; value: number }) {
  const color = value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex-1">
      <div className="flex justify-between text-[9px] text-gray-500 mb-0.5">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-1 rounded-full bg-gray-700">
        <div className={`h-1 rounded-full ${color} transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
