"use client";

import React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Clock3,
  MessageSquare,
  Phone,
  PhoneCall,
  PhoneIncoming,
  PhoneMissed,
  RefreshCw,
  Send,
} from "lucide-react";
import { useTelephony } from "@/lib/telephony-context";
import { LiveTranscript } from "@/components/transcription/live-transcript";
import { CoachPanel } from "@/components/transcription/coach-panel";
import { PostCallPreview } from "@/components/transcription/postcall-preview";

type HistoryItem = {
  id: string;
  kind: "call" | "sms";
  direction: "inbound" | "outbound";
  status: string;
  phone_number: string;
  timestamp: string;
  duration_seconds: number;
  preview: string;
};

type HistoryResponse = {
  phone_number: string;
  items: HistoryItem[];
  total: number;
};

type HistoryFilter = "all" | "calls" | "texts" | "missed";

const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"];
const PNS_SMS_COMPLIANCE_FOOTER = "Pacific North Systems, 2485 West Broadway, Vancouver, BC V6K 2E8, Canada. pacificnorthsystems.com. Reply STOP to opt out.";
const NEVER_MISS_FOLLOW_UP = "Hi, it’s Vini from Pacific North Systems. Thanks for taking my call. Never Miss helps contractors follow up only when a customer call goes unanswered: the caller receives a quick text, their reply is captured, and you get a callback task in one place. You can see how it works and start a 30-day free trial here: https://www.pacificnorthsystems.com/never-miss\n\nIf you have questions, reply here and I’ll help.";

function normalizePhone(value: string) {
  const trimmed = value.trim();
  const digits = trimmed.replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  if (trimmed.startsWith("+")) return `+${digits}`;
  return digits ? `+${digits}` : "";
}

function formatPhone(value: string) {
  const digits = value.replace(/\D/g, "");
  const local = digits.length === 11 && digits.startsWith("1") ? digits.slice(1) : digits;
  if (local.length === 10) return `(${local.slice(0, 3)}) ${local.slice(3, 6)} ${local.slice(6)}`;
  return value || "No number selected";
}

function formatTime(value: string) {
  const date = new Date(value);
  return new Intl.DateTimeFormat("en-CA", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function formatDuration(seconds: number) {
  if (!seconds) return "";
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${remainder.toString().padStart(2, "0")}`;
}

function withPnsSmsFooter(message: string) {
  if (message.includes(PNS_SMS_COMPLIANCE_FOOTER)) return message.trim();
  return `${message.trim()}\n\n${PNS_SMS_COMPLIANCE_FOOTER}`;
}

export default function CallCenterScreen() {
  const { call, startCall, transcription, transcriptId } = useTelephony();
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<HistoryResponse>({ phone_number: "+16042251745", items: [], total: 0 });
  const [filter, setFilter] = useState<HistoryFilter>("all");
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [followUpMessage, setFollowUpMessage] = useState(NEVER_MISS_FOLLOW_UP);
  const [followUpSending, setFollowUpSending] = useState(false);
  const [scriptOpen, setScriptOpen] = useState(true);
  const browserCallId = useRef<number | null>(null);
  const lastRecordedState = useRef("");

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const response = await fetch("/api/telephony/history", { cache: "no-store" });
      if (!response.ok) throw new Error("Communication history is temporarily unavailable");
      setHistory(await response.json());
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : "Communication history is temporarily unavailable");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    const id = browserCallId.current;
    if (!id || !["connected", "ended", "failed"].includes(call.state) || lastRecordedState.current === call.state) return;
    lastRecordedState.current = call.state;
    void fetch(`/api/telephony/calls/browser/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: call.state, duration_seconds: call.duration }),
    }).then(() => {
      if (["ended", "failed"].includes(call.state)) {
        browserCallId.current = null;
        window.setTimeout(() => void loadHistory(), 500);
      }
    }).catch(() => {});
  }, [call.duration, call.state, loadHistory]);

  const selectedItems = useMemo(() => history.items.filter((item) => {
    if (filter === "calls") return item.kind === "call";
    if (filter === "texts") return item.kind === "sms";
    if (filter === "missed") return item.kind === "call" && item.status === "missed";
    return true;
  }), [filter, history.items]);

  const activeCall = ["dialing", "ringing", "connected", "muted", "on_hold", "recording"].includes(call.state);
  const validPhone = normalizePhone(phone).replace(/\D/g, "").length >= 10;
  const connectedOutboundCall = useMemo(() => history.items.find((item) => (
    item.kind === "call"
    && item.direction === "outbound"
    && item.status === "connected"
    && normalizePhone(item.phone_number) === normalizePhone(phone)
  )), [history.items, phone]);

  const addKey = (key: string) => {
    setActionMessage("");
    setPhone((current) => `${current}${key}`.slice(0, 18));
  };

  const placeCall = async () => {
    if (!validPhone || activeCall) return;
    setActionMessage("Opening your microphone and starting the call");
    try {
      const response = await fetch("/api/telephony/calls/browser", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: normalizePhone(phone) }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || result.detail || "The call could not be prepared");
      browserCallId.current = result.id;
      lastRecordedState.current = "dialing";
      await startCall(0, normalizePhone(phone), "", "", result.id);
      window.setTimeout(() => void loadHistory(), 1200);
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : "The call could not be started");
    }
  };

  const sendText = async () => {
    if (!validPhone || !message.trim() || sending) return;
    setSending(true);
    setActionMessage("Sending your text message");
    try {
      const response = await fetch("/api/telephony/sms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: normalizePhone(phone), message: withPnsSmsFooter(message) }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || result.detail || "The text message could not be sent");
      setMessage("");
      setActionMessage("Text sent successfully");
      await loadHistory();
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : "The text message could not be sent");
    } finally {
      setSending(false);
    }
  };

  const sendNeverMissFollowUp = async () => {
    if (!connectedOutboundCall || !validPhone || !followUpMessage.trim() || followUpSending) return;
    setFollowUpSending(true);
    setActionMessage("Sending Never Miss details");
    try {
      const response = await fetch("/api/telephony/sms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: normalizePhone(phone), message: withPnsSmsFooter(followUpMessage) }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || result.detail || "The follow-up could not be sent");
      setActionMessage("Never Miss details sent successfully");
      await loadHistory();
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : "The follow-up could not be sent");
    } finally {
      setFollowUpSending(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Command Center</p>
          <h1 className="mt-1 text-3xl font-semibold text-white">Call Center Phone</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Call, text and review every conversation handled through the Pacific North Systems number.
          </p>
        </div>
        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3">
          <p className="text-xs text-cyan-200">PNS business line</p>
          <p className="mt-1 font-semibold text-white">{formatPhone(history.phone_number)}</p>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
        <div className="space-y-6">
          <section className="rounded-3xl border border-white/10 bg-slate-950/70 p-5 shadow-2xl shadow-black/20">
            <label htmlFor="call-center-number" className="text-sm font-medium text-slate-200">Phone number</label>
            <div className="mt-2 flex gap-2">
              <input
                id="call-center-number"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="Enter any Canadian or US number"
                inputMode="tel"
                className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-lg font-semibold text-white outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/20"
              />
              <button
                type="button"
                onClick={() => setPhone("")}
                className="rounded-2xl border border-white/10 px-3 text-sm text-slate-400 hover:bg-white/5 hover:text-white"
              >
                Clear
              </button>
            </div>
            <p className="mt-2 min-h-5 text-sm text-cyan-200">{formatPhone(normalizePhone(phone))}</p>

            <div className="mt-4 grid grid-cols-3 gap-3" aria-label="Phone keypad">
              {KEYS.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => addKey(key)}
                  className="rounded-2xl border border-white/10 bg-white/5 py-3 text-xl font-semibold text-white transition hover:border-cyan-300/40 hover:bg-cyan-300/10"
                >
                  {key}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => void placeCall()}
              disabled={!validPhone || activeCall}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-500 px-4 py-3 font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <PhoneCall className="h-5 w-5" />
              {activeCall ? "Call in progress" : "Call this number"}
            </button>
            <p className="mt-3 text-center text-xs text-slate-500">
              Your browser will ask for microphone access before the first call.
            </p>
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-cyan-300" />
              <h2 className="text-lg font-semibold text-white">Send a text</h2>
            </div>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value.slice(0, 1000))}
              placeholder="Write a helpful message"
              rows={4}
              className="mt-4 w-full resize-none rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/20"
            />
            <div className="mt-2 flex items-center justify-between gap-3 text-xs text-slate-500">
              <span>Only text people who expect to hear from PNS.</span>
              <span>{message.length}/1000</span>
            </div>
            <button
              type="button"
              onClick={() => void sendText()}
              disabled={!validPhone || !message.trim() || sending}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
              {sending ? "Sending" : "Send text"}
            </button>
          </section>

          {connectedOutboundCall && (
            <section className="rounded-3xl border border-emerald-400/20 bg-emerald-400/5 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-300">Post-call follow-up</p>
              <h2 className="mt-1 text-lg font-semibold text-white">Send Never Miss details</h2>
              <p className="mt-2 text-sm text-slate-400">This call connected. Send only when the person asked to receive the details.</p>
              <textarea
                value={followUpMessage}
                onChange={(event) => setFollowUpMessage(event.target.value.slice(0, 1000))}
                aria-label="Never Miss follow-up message"
                rows={7}
                className="mt-4 w-full resize-y rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none transition focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/20"
              />
              <button
                type="button"
                onClick={() => void sendNeverMissFollowUp()}
                disabled={!followUpMessage.trim() || followUpSending}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-500 px-4 py-3 font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
                {followUpSending ? "Sending" : "Send Never Miss details"}
              </button>
            </section>
          )}

          {actionMessage && (
            <div role="status" className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-100">
              {actionMessage}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {(activeCall || transcriptId) && (
            <section className="rounded-3xl border border-cyan-400/20 bg-slate-950/70 p-6 shadow-2xl shadow-black/20">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-300">Live call tools</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Transcript and AI call guide</h2>
                </div>
                <p className="text-xs text-slate-400">Confirm recording consent before discussing customer details.</p>
              </div>
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(380px,0.9fr)]">
                <LiveTranscript state={transcription} onStop={() => {}} expanded />
                <CoachPanel callId={call.callId} isCallActive={activeCall} segments={transcription.segments || []} expanded />
              </div>
            </section>
          )}

          {(call.state === "ended" || call.state === "failed") && transcriptId && (
            <PostCallPreview transcriptId={transcriptId} callId={call.callId} />
          )}

          <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/5">
            <button
              type="button"
              onClick={() => setScriptOpen((value) => !value)}
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left hover:bg-white/5"
              aria-expanded={scriptOpen}
            >
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-300">Conversation guide</p>
                <h2 className="mt-1 text-lg font-semibold text-white">Simple PNS call script</h2>
              </div>
              {scriptOpen ? <ChevronUp className="h-5 w-5 text-slate-400" /> : <ChevronDown className="h-5 w-5 text-slate-400" />}
            </button>
            {scriptOpen && (
              <div className="grid gap-4 border-t border-white/10 p-5 md:grid-cols-2">
                <ScriptStep number="1" title="Open naturally">
                  Hi, this is Vini from Pacific North Systems. Did I catch you at an okay time for a quick question?
                </ScriptStep>
                <ScriptStep number="2" title="Learn about their work">
                  I am curious how your team currently handles follow ups, paperwork, scheduling or repeated data entry.
                </ScriptStep>
                <ScriptStep number="3" title="Find the real cost">
                  Where does the process slow down most? How often does information get missed or entered more than once?
                </ScriptStep>
                <ScriptStep number="4" title="Connect the value">
                  We build practical systems that remove repetitive work and help teams respond to customers faster.
                </ScriptStep>
                <ScriptStep number="5" title="Offer a useful next step">
                  Would a short operations review be useful? We can map the process and show where automation could save time.
                </ScriptStep>
                <ScriptStep number="6" title="Close clearly">
                  Great. I will send a short confirmation now. What is the best email and time for us to continue?
                </ScriptStep>
              </div>
            )}
          </section>

          <section className="rounded-3xl border border-white/10 bg-slate-950/50 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-300">PNS communication log</p>
                <h2 className="mt-1 text-xl font-semibold text-white">Calls and text messages</h2>
              </div>
              <button
                type="button"
                onClick={() => void loadHistory()}
                disabled={historyLoading}
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300 hover:bg-white/5 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${historyLoading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {(["all", "calls", "texts", "missed"] as HistoryFilter[]).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setFilter(value)}
                  className={`rounded-xl px-3 py-2 text-sm font-medium capitalize transition ${
                    filter === value ? "bg-cyan-400 text-slate-950" : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>

            <div className="mt-5 space-y-3">
              {historyLoading && <p className="py-8 text-center text-sm text-slate-500">Loading communication history</p>}
              {!historyLoading && historyError && <p className="rounded-2xl bg-red-500/10 px-4 py-3 text-sm text-red-200">{historyError}</p>}
              {!historyLoading && !historyError && selectedItems.length === 0 && (
                <p className="py-8 text-center text-sm text-slate-500">No conversations match this view yet.</p>
              )}
              {!historyLoading && !historyError && selectedItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setPhone(item.phone_number)}
                  className="flex w-full items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-cyan-400/30 hover:bg-cyan-400/5"
                >
                  <HistoryIcon item={item} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-white">{formatPhone(item.phone_number)}</p>
                      <p className="inline-flex items-center gap-1 text-xs text-slate-500">
                        <Clock3 className="h-3 w-3" /> {formatTime(item.timestamp)}
                      </p>
                    </div>
                    <p className="mt-1 truncate text-sm text-slate-400">{item.preview}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                      <span className="capitalize">{item.direction}</span>
                      <span>•</span>
                      <span className={item.status === "missed" ? "text-red-300" : "capitalize"}>{item.status.replaceAll("_", " ")}</span>
                      {item.duration_seconds > 0 && <><span>•</span><span>{formatDuration(item.duration_seconds)}</span></>}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function ScriptStep({ number, title, children }: { number: string; title: string; children: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
      <div className="flex items-center gap-3">
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-cyan-400 text-xs font-bold text-slate-950">{number}</span>
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">{children}</p>
    </div>
  );
}

function HistoryIcon({ item }: { item: HistoryItem }) {
  if (item.kind === "sms") {
    return <span className="rounded-xl bg-cyan-400/10 p-2 text-cyan-300"><MessageSquare className="h-4 w-4" /></span>;
  }
  if (item.status === "missed") {
    return <span className="rounded-xl bg-red-400/10 p-2 text-red-300"><PhoneMissed className="h-4 w-4" /></span>;
  }
  if (item.direction === "inbound") {
    return <span className="rounded-xl bg-amber-400/10 p-2 text-amber-300"><PhoneIncoming className="h-4 w-4" /></span>;
  }
  return <span className="rounded-xl bg-emerald-400/10 p-2 text-emerald-300"><Phone className="h-4 w-4" /></span>;
}
