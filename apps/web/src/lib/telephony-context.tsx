"use client";

import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import {
  initWebRTC,
  makeCall as wrtcMakeCall,
  hangupCall as wrtcHangup,
  disconnect as wrtcDisconnect,
  muteCall,
  unmuteCall,
  holdCall as wrtcHold,
  resumeCall as wrtcResume,
  setVolume,
  setSpeaker,
  setTokenRefreshCallback,
  getDiagnostics,
  getMicrophoneStream,
  getRemoteStream,
  onCallStateChange,
  type WrtcCallState,
  type WrtcDiagnostics,
} from "@/lib/webrtc-client";
import { useTranscription, type TranscriptionState } from "@/lib/transcription";

// ── Types ──

export type CallState =
  | "idle" | "registering" | "dialing" | "ringing"
  | "connected" | "muted" | "on_hold" | "recording"
  | "ended" | "failed";

export type ActiveCall = {
  callId: number | null;
  state: CallState;
  companyId: number | null;
  companyName: string;
  contactName: string;
  phoneNumber: string;
  duration: number;
  muted: boolean;
  held: boolean;
  recording: boolean;
  error: string;
  registered: boolean;
  connectionQuality: "good" | "fair" | "poor";
};

type TelephonyContextValue = {
  call: ActiveCall;
  startCall: (companyId: number, phoneNumber: string, companyName?: string, contactName?: string) => Promise<void>;
  endCall: () => Promise<void>;
  toggleMute: () => Promise<void>;
  toggleHold: () => Promise<void>;
  toggleRecording: () => Promise<void>;
  resetCall: () => void;
  setMinimized: (v: boolean) => void;
  setVolume: (v: number) => void;
  setSpeaker: (deviceId: string) => Promise<void>;
  isMinimized: boolean;
  diagnostics: WrtcDiagnostics;
  transcription: TranscriptionState;
  transcriptId: number | null;
};

// ── Context ──

const TelephonyContext = createContext<TelephonyContextValue | null>(null);

export function useTelephony(): TelephonyContextValue {
  const ctx = useContext(TelephonyContext);
  if (!ctx) throw new Error("useTelephony must be used within TelephonyProvider");
  return ctx;
}

// ── Phone normalization ──

function normalizePhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  if (phone.startsWith("+")) return phone;
  return `+${digits}`; // best effort
}

// ── Provider ──

export function TelephonyProvider({ children }: { children: ReactNode }) {
  const [call, setCall] = useState<ActiveCall>({
    callId: null, state: "idle", companyId: null,
    companyName: "", contactName: "", phoneNumber: "",
    duration: 0, muted: false, held: false, recording: false,
    error: "", registered: false, connectionQuality: "good",
  });
  const [isMinimized, setMinimized] = useState(false);
  const [diagnostics, setDiagnostics] = useState<WrtcDiagnostics>(getDiagnostics());
  const [transcriptId, setTranscriptId] = useState<number | null>(null);
  const tokenRef = useRef<string | null>(null);
  const wrtcCallIdRef = useRef<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const prevStateRef = useRef<CallState>("idle");

  // ── Transcription hook ──
  const transcription = useTranscription();

  // ── Token refresh callback for reconnect ──

  useEffect(() => {
    setTokenRefreshCallback(async () => {
      const r = await fetch("/api/telephony/register", { method: "POST" });
      if (!r.ok) throw new Error(`Token refresh failed (${r.status})`);
      const d = await r.json();
      if (!d.token) throw new Error("No token in refresh response");
      tokenRef.current = d.token;
      return d.token; // base64-encoded, initWebRTC will decode
    });
  }, []);

  // ── WebRTC init ──

  useEffect(() => {
    // Subscribe to call state changes from WebRTC client
    onCallStateChange((wrtcState, callId) => {
      const map: Record<WrtcCallState, CallState> = {
        idle: "idle", dialing: "dialing", ringing: "ringing",
        answered: "connected", active: "connected",
        held: "on_hold", hangup: "ended", destroy: "ended", error: "failed",
      };
      const mapped = map[wrtcState] || "idle";
      setCall(c => ({ ...c, state: mapped }));
      if (wrtcState === "active") {
        setCall(c => ({ ...c, duration: 0 }));
      }
      // Capture WebRTC call ID for coach/transcription
      if (callId) {
        wrtcCallIdRef.current = callId;
      }
    });

    // Update diagnostics periodically
    const diagInterval = setInterval(() => setDiagnostics(getDiagnostics()), 2000);
    return () => clearInterval(diagInterval);
  }, []);

  // ── Duration timer ──

  useEffect(() => {
    const active = call.state === "connected" && !call.held;
    if (active) {
      timerRef.current = setInterval(() => setCall(c => ({ ...c, duration: c.duration + 1 })), 1000);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [call.state, call.held]);

  // ── Transcription: auto-start on connect, auto-stop on end ──

  useEffect(() => {
    const prev = prevStateRef.current;
    prevStateRef.current = call.state;

    // Start transcription when call becomes connected — TWO independent sessions
    if (prev !== "connected" && call.state === "connected") {
      const micStream = getMicrophoneStream();
      if (micStream) {
        transcription.startSession(call.callId, call.companyId, micStream, "agent");
      }
      // Start prospect session with delay (remote track may not be available immediately)
      setTimeout(() => {
        const remoteStream = getRemoteStream();
        if (remoteStream && remoteStream.getAudioTracks().length > 0) {
          transcription.startSession(call.callId, call.companyId, remoteStream, "prospect");
        } else {
          console.warn("[Telephony] Remote audio stream not available for transcription");
        }
      }, 1500);
    }

    // Stop transcription and trigger post-call when call ends
    if (prev === "connected" && (call.state === "ended" || call.state === "failed")) {
      transcription.stopAll();

      // Trigger post-call intelligence generation (only if we have a valid transcript ID)
      const tid = transcription.transcriptId || transcriptId;
      if (tid && typeof tid === "number") {
        fetch(`/api/sales-coach/postcall/generate/${tid}`, { method: "POST" })
          .then(r => r.ok ? r.json() : null)
          .catch(() => {});
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [call.state, call.callId]);

  // Track transcriptId from transcription hook (updates asynchronously after start)
  useEffect(() => {
    if (transcription.transcriptId && !transcriptId) {
      setTranscriptId(transcription.transcriptId);
    }
  }, [transcription.transcriptId, transcriptId]);

  // ── Actions ──

  const startCall = useCallback(async (
    companyId: number, phoneNumber: string, companyName = "", contactName = "",
  ) => {
    if (!phoneNumber.trim()) return;
    setCall(c => ({ ...c, state: "dialing", companyId, companyName, contactName, phoneNumber, error: "", duration: 0 }));
    setMinimized(false);

    try {
      // 0. Pre-load company context for AI coach
      fetch(`/api/companies/${companyId}`, { method: "GET" }).catch(() => {});

      // 1. Get WebRTC token from backend
      let token = tokenRef.current;
      if (!token) {
        const r = await fetch("/api/telephony/register", { method: "POST" });
        if (!r.ok) throw new Error(`Registration failed (${r.status})`);
        const d = await r.json();
        if (!d.token) throw new Error("No token received");
        token = d.token;
        tokenRef.current = token;
      }

      if (!token) throw new Error("No WebRTC token");
      // 2. Initialize WebRTC client — decode base64 token into login:password for SDK
      const decoded = atob(token);
      const colonIdx = decoded.indexOf(":");
      if (colonIdx === -1) throw new Error("Invalid token format");
      const login = decoded.slice(0, colonIdx);
      const password = decoded.slice(colonIdx + 1);
      await initWebRTC(login, password);

      // 3. Normalize phone to E.164 (+1XXXXXXXXXX) — Telnyx rejects non-E.164 numbers
      const normalizedPhone = normalizePhone(phoneNumber);

      // 4. Make WebRTC call — the SDK handles PSTN bridging through the SIP connection.
      //    No server-side REST API call needed for Click-to-Call WebRTC.
      const callerNumber = "+16042251745"; // Telnyx phone number as caller ID
      await wrtcMakeCall(normalizedPhone, callerNumber, companyName);
      setCall(c => ({ ...c, state: "ringing" }));

    } catch (e) {
      setCall(c => ({ ...c, state: "failed", error: e instanceof Error ? e.message : "Call failed" }));
    }
  }, []);

  const endCall = useCallback(async () => {
    await wrtcHangup();
    if (tokenRef.current) {
      wrtcDisconnect();
      tokenRef.current = null;
    }
    if (call.callId) {
      try { await fetch(`/api/telephony/call/${call.callId}/end`, { method: "POST" }); } catch { /* noop */ }
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setCall(c => ({ ...c, state: "ended", recording: false, held: false }));
    setTimeout(() => {
      setCall(prev => {
        if (prev.state === "ended" || prev.state === "failed") {
          return {
            callId: null, state: "idle", companyId: null,
            companyName: "", contactName: "", phoneNumber: "",
            duration: 0, muted: false, held: false, recording: false,
            error: "", registered: true, connectionQuality: "good",
          };
        }
        return prev;
      });
    }, 3000);
  }, [call.callId]);

  const toggleMute = useCallback(async () => {
    const newMuted = !call.muted;
    if (newMuted) muteCall(); else unmuteCall();
    setCall(c => ({ ...c, muted: newMuted, state: newMuted ? "muted" : call.recording ? "recording" : "connected" }));
    if (call.callId) {
      try {
        await fetch(`/api/telephony/call/${call.callId}/${newMuted ? "mute" : "unmute"}`, { method: "POST" });
      } catch { /* noop */ }
    }
  }, [call.muted, call.recording, call.callId]);

  const toggleHold = useCallback(async () => {
    const newHeld = !call.held;
    if (newHeld) wrtcHold(); else wrtcResume();
    setCall(c => ({ ...c, held: newHeld, state: newHeld ? "on_hold" : call.muted ? "muted" : call.recording ? "recording" : "connected" }));
    if (call.callId) {
      try {
        await fetch(`/api/telephony/call/${call.callId}/${newHeld ? "hold" : "resume"}`, { method: "POST" });
      } catch { /* noop */ }
    }
  }, [call.held, call.muted, call.recording, call.callId]);

  const toggleRecording = useCallback(async () => {
    if (!call.callId) return;
    const newRec = !call.recording;
    setCall(c => ({ ...c, recording: newRec, state: newRec ? "recording" : call.muted ? "muted" : "connected" }));
    try {
      if (newRec) await fetch(`/api/telephony/call/${call.callId}/recording/start`, { method: "POST" });
      else await fetch(`/api/telephony/call/${call.callId}/recording/stop`, { method: "POST" });
    } catch { /* noop */ }
  }, [call.recording, call.muted, call.callId]);

  const resetCall = useCallback(() => {
    setCall({
      callId: null, state: "idle", companyId: null,
      companyName: "", contactName: "", phoneNumber: "",
      duration: 0, muted: false, held: false, recording: false,
      error: "", registered: true, connectionQuality: "good",
    });
  }, []);

  return (
    <TelephonyContext.Provider value={{ call, startCall, endCall, toggleMute, toggleHold, toggleRecording, resetCall, setMinimized, isMinimized, diagnostics, setVolume, setSpeaker, transcription, transcriptId }}>
      {children}
    </TelephonyContext.Provider>
  );
}
