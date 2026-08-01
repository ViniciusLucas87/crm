"use client";

import { useState, useEffect } from "react";
import { Clock, User, MessageSquare } from "lucide-react";
import { Card } from "@/components/ui/card";

type Utterance = {
  id: number;
  speaker: string;
  speaker_label?: string | null;
  text: string;
  confidence: number;
  start_seconds: number;
  end_seconds: number;
  words: Array<{ word: string; start: number; end: number }>;
};

type TranscriptData = {
  id: number;
  call_id?: number | null;
  company_id?: number | null;
  provider: string;
  language: string;
  status: string;
  full_text?: string | null;
  word_count: number;
  utterance_count: number;
  started_at?: string | null;
  ended_at?: string | null;
  duration_seconds: number;
  utterances: Utterance[];
};

type Props = {
  transcriptId: number | null;
};

export function ConversationTimeline({ transcriptId }: Props) {
  const [data, setData] = useState<TranscriptData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activeUtterance, setActiveUtterance] = useState<number | null>(null);

  useEffect(() => {
    if (!transcriptId) return;
    setLoading(true);
    fetch(`/api/transcription/transcripts/${transcriptId}`)
      .then(r => r.json())
      .then(d => {
        if (d.error) setError(d.error);
        else setData(d);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [transcriptId]);

  if (!transcriptId) return null;
  if (loading) return <Card className="p-4 bg-gray-900"><div className="text-gray-400 text-sm">Loading transcript...</div></Card>;
  if (error) return <Card className="p-4 bg-gray-900"><div className="text-red-400 text-sm">[Timeline] {error}</div></Card>;
  if (!data) return null;

  const filtered = search
    ? data.utterances.filter(u => u.text.toLowerCase().includes(search.toLowerCase()))
    : data.utterances;

  return (
    <Card className="flex flex-col h-full bg-gray-900 border-gray-700">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-200">Conversation Timeline</h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-gray-500">
          <span>{data.provider}</span>
          <span>·</span>
          <span>{data.utterance_count} utterances</span>
          <span>·</span>
          <span>{formatDuration(data.duration_seconds)}</span>
        </div>
      </div>

      <div className="px-4 py-2 border-b border-gray-700">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search utterances..."
          className="w-full px-3 py-1.5 text-xs rounded-lg bg-gray-800 border border-gray-600 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-400/50"
        />
      </div>

      <div className="px-4 py-2 flex items-center gap-3 text-[10px] text-gray-400 border-b border-gray-700">
        <span className={`px-1.5 py-0.5 rounded ${data.status === "completed" ? "bg-emerald-400/10 text-emerald-400" : "bg-amber-400/10 text-amber-400"}`}>
          {data.status === "completed" ? "✓ Completed" : "In Progress"}
        </span>
        {data.started_at && <span>{new Date(data.started_at).toLocaleString()}</span>}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[600px]">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-sm gap-2">
            <MessageSquare className="w-8 h-8 opacity-30" />
            No utterances found
          </div>
        )}

        {filtered.map((u) => {
          const isActive = activeUtterance === u.id;
          return (
            <div
              key={u.id}
              role="button"
              tabIndex={0}
              className={`relative pl-6 border-l-2 transition-colors cursor-pointer ${
                isActive ? "border-emerald-400" : "border-gray-700 hover:border-gray-500"
              }`}
              onClick={() => setActiveUtterance(isActive ? null : u.id)}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setActiveUtterance(isActive ? null : u.id); }}
            >
              <div className={`absolute left-[-5px] top-1 w-2 h-2 rounded-full ${isActive ? "bg-emerald-400" : "bg-gray-600"}`} />
              <span className="text-[10px] text-gray-500 font-mono">{formatTime(u.start_seconds)}</span>

              <div className="flex items-center gap-1.5 mb-1">
                <User className="w-3 h-3 text-gray-400" />
                <span className="text-[11px] font-semibold text-gray-300">{u.speaker_label || u.speaker}</span>
              </div>

              <p className="text-sm text-gray-200 leading-relaxed mb-2">{u.text}</p>

              {isActive && (
                <div className="mt-2 p-2 rounded-lg bg-gray-800 space-y-1 text-[10px] text-gray-400">
                  <div className="flex justify-between">
                    <span>Confidence: {Math.round(u.confidence * 100)}%</span>
                    <span>Duration: {(u.end_seconds - u.start_seconds).toFixed(1)}s</span>
                  </div>
                  {u.words && u.words.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {u.words.map((w, i) => (
                        <span key={i} className="px-1 py-0.5 rounded bg-gray-700 text-gray-300 hover:bg-emerald-900/50 hover:text-emerald-300 transition-colors cursor-pointer" title={`${formatTime(w.start)} - ${formatTime(w.end)}`}>
                          {w.word}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {data.full_text && (
        <div className="px-4 py-3 border-t border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-[10px] font-semibold text-gray-400 uppercase">Full Transcript</span>
          </div>
          <p className="text-xs text-gray-500 line-clamp-3">{data.full_text}</p>
        </div>
      )}
    </Card>
  );
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}
