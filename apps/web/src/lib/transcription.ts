"use client";

/**
 * Live Transcription Client — Dual-Channel with State Machine (Sprint 47.3)
 *
 * PART 1: Idempotent startup state machine per channel
 * PART 2-3: Structured pipeline instrumentation
 * PART 7: Two independent channels, session uniqueness
 * PART 9: Transcript reconciliation
 * PART 13: Per-channel health state
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { PcmAudioProcessor, type AudioSourceRole, type PcmDiagnostics } from "@/lib/pcm-processor";

// ═══════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════

export type TranscriptWord = {
  word: string;
  start: number;
  end: number;
  confidence?: number;
};

export type TranscriptSegment = {
  id: string;
  speaker: string;
  text: string;
  start: number;
  end: number;
  confidence: number;
  isFinal: boolean;
  words: TranscriptWord[];
  utteranceNumber?: number;
  sourceRole?: AudioSourceRole;
};

export type TranscriptionPhase =
  | "idle" | "initializing" | "connecting" | "listening"
  | "streaming" | "processing" | "completed" | "archived";

/** Per-channel health state (PART 13) */
export type ChannelHealth =
  | "waiting"
  | "connecting"
  | "streaming"
  | "silent"
  | "unavailable"
  | "failed"
  | "stopped";

/** Per-channel state machine (PART 1) */
type ChannelState =
  | "idle"
  | "socket_connecting"
  | "socket_open"
  | "processor_starting"
  | "streaming"
  | "stopping"
  | "stopped"
  | "failed";

type ChannelSession = {
  role: AudioSourceRole;
  state: ChannelState;
  ws: WebSocket | null;
  processor: PcmAudioProcessor | null;
  sessionId: string;
  transcriptId: number | null;
  speakerLabel: string;
  startPromise: Promise<void> | null;
  processorStarted: boolean;
  socketOpened: boolean;
  stopRequested: boolean;
  sessionGeneration: number;
  callId: number | null;
  // Diagnostics
  chunkCount: number;
  bytesSent: number;
  interimCount: number;
  finalCount: number;
  lastAudioAt: number;
  lastTranscriptAt: number;
  errorCode: string | null;
  deepgramState: string;
  correlationId: string;
};

export type TranscriptionState = {
  phase: TranscriptionPhase;
  isConnected: boolean;
  isStreaming: boolean;
  sessionId: string | null;
  transcriptId: number | null;
  segments: TranscriptSegment[];
  fullText: string;
  error: string | null;
  provider: string;
  wordCount: number;
  activeSessions: AudioSourceRole[];
  agentHealth: ChannelHealth;
  prospectHealth: ChannelHealth;
  agentDiagnostics: PcmDiagnostics | null;
  prospectDiagnostics: PcmDiagnostics | null;
};

const INITIAL_STATE: TranscriptionState = {
  phase: "idle", isConnected: false, isStreaming: false,
  sessionId: null, transcriptId: null,
  segments: [], fullText: "", error: null, provider: "", wordCount: 0,
  activeSessions: [],
  agentHealth: "waiting", prospectHealth: "waiting",
  agentDiagnostics: null, prospectDiagnostics: null,
};

// ═══════════════════════════════════════════════════
// Hook
// ═══════════════════════════════════════════════════

export function useTranscription() {
  const [state, setState] = useState<TranscriptionState>(INITIAL_STATE);
  const channelsRef = useRef<Map<AudioSourceRole, ChannelSession>>(new Map());
  const segmentsRef = useRef<TranscriptSegment[]>([]);
  const fullTextRef = useRef("");
  const activeCallIdRef = useRef<number | null>(null);

  // ── State helpers ──

  const setChannelHealth = useCallback((role: AudioSourceRole, health: ChannelHealth) => {
    setState(s => ({
      ...s,
      [role === "agent" ? "agentHealth" : "prospectHealth"]: health,
    }));
  }, []);

  const flushSegments = useCallback(() => {
    setState(s => ({
      ...s,
      segments: [...segmentsRef.current],
      fullText: fullTextRef.current.trim(),
      wordCount: fullTextRef.current.trim().split(/\s+/).filter(Boolean).length,
    }));
  }, []);

  const logDiag = useCallback((channel: ChannelSession, msg: string) => {
    console.log(
      `[Transcription:${channel.role}] ${msg} — ` +
      `state=${channel.state} chunks=${channel.chunkCount} interim=${channel.interimCount} final=${channel.finalCount} ` +
      `correlation=${channel.correlationId}`
    );
  }, []);

  // ── PART 9: Transcript reconciliation ──

  const upsertSegment = useCallback((seg: TranscriptSegment) => {
    const utteranceKey = `${seg.speaker}-${seg.id}`;

    if (seg.isFinal) {
      const dupIdx = segmentsRef.current.findIndex(s =>
        s.isFinal && s.speaker === seg.speaker && s.text === seg.text
      );
      if (dupIdx >= 0) return;
    }

    const existingIdx = segmentsRef.current.findIndex(s =>
      `${s.speaker}-${s.id}` === utteranceKey
    );

    if (existingIdx >= 0) {
      const existing = segmentsRef.current[existingIdx];
      if (seg.isFinal || !existing.isFinal) {
        segmentsRef.current[existingIdx] = seg;
      }
    } else {
      segmentsRef.current.push(seg);
    }

    if (seg.isFinal) {
      fullTextRef.current = segmentsRef.current
        .filter(s => s.isFinal)
        .map(s => s.text)
        .join(" ") + " ";
    }

    flushSegments();
  }, [flushSegments]);

  // ── Cleanup ──

  const cleanupChannel = useCallback((channel: ChannelSession) => {
    channel.stopRequested = true;
    channel.state = "stopping";
    if (channel.processor) {
      try { channel.processor.stop(); } catch { /* noop */ }
      channel.processor = null;
    }
    if (channel.ws) {
      try { channel.ws.close(); } catch { /* noop */ }
      channel.ws = null;
    }
    channel.state = "stopped";
    channelsRef.current.delete(channel.role);
  }, []);

  const cleanupAll = useCallback(() => {
    for (const ch of channelsRef.current.values()) {
      cleanupChannel(ch);
    }
  }, [cleanupChannel]);

  useEffect(() => { return cleanupAll; }, [cleanupAll]);

  // ── PART 1: Idempotent startup state machine ──

  const startSession = useCallback(async (
    callId: number | null,
    companyId: number | null,
    audioStream: MediaStream,
    role: AudioSourceRole,
  ): Promise<void> => {
    // Guard: already active for this role
    const existing = channelsRef.current.get(role);
    if (existing) {
      if (existing.state === "streaming" || existing.state === "processor_starting") {
        logDiag(existing, "startSession skipped — already active");
        return existing.startPromise || Promise.resolve();
      }
      if (existing.state === "socket_connecting" || existing.state === "socket_open") {
        logDiag(existing, "startSession skipped — connection in progress, returning existing promise");
        return existing.startPromise || Promise.resolve();
      }
      // State is stopped/failed — clean up stale entry
      cleanupChannel(existing);
    }

    // Guard: same callId? If a new call started, clean old channels
    if (activeCallIdRef.current !== null && activeCallIdRef.current !== callId) {
      cleanupAll();
      segmentsRef.current = [];
      fullTextRef.current = "";
      setState(s => ({ ...s, segments: [], fullText: "", wordCount: 0 }));
    }
    activeCallIdRef.current = callId;

    const correlationId = `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    const speakerLabel = role === "agent" ? "PNS Agent" : "Prospect";
    const sessionGeneration = Date.now();

    const channel: ChannelSession = {
      role,
      state: "idle",
      ws: null,
      processor: null,
      sessionId: "",
      transcriptId: null,
      speakerLabel,
      startPromise: null,
      processorStarted: false,
      socketOpened: false,
      stopRequested: false,
      sessionGeneration,
      callId,
      chunkCount: 0,
      bytesSent: 0,
      interimCount: 0,
      finalCount: 0,
      lastAudioAt: 0,
      lastTranscriptAt: 0,
      errorCode: null,
      deepgramState: "disconnected",
      correlationId,
    };

    const startPromise = (async () => {
      try {
        // ── 1. REST: Start transcription session ──
        channel.state = "idle";
        setChannelHealth(role, "connecting");
        setState(s => ({
          ...s, error: null, isStreaming: true,
          activeSessions: [...s.activeSessions.filter(r => r !== role), role],
        }));

        const params = new URLSearchParams();
        if (callId) params.set("call_id", String(callId));
        if (companyId) params.set("company_id", String(companyId));
        params.set("source_role", role);
        const r = await fetch(`/api/transcription/start?${params.toString()}`, { method: "POST" });
        if (!r.ok) throw new Error(`Failed to start ${role} transcription (${r.status})`);
        const { session_id: sessionId, transcript_id: transcriptId, provider } = await r.json();
        channel.sessionId = sessionId;
        channel.transcriptId = transcriptId;

        setState(s => ({
          ...s, sessionId, transcriptId: transcriptId || s.transcriptId,
          provider: provider || s.provider || "",
        }));

        // ── 2. WebSocket ──
        channel.state = "socket_connecting";
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const apiHost = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/^https?:\/\//, "");
        const wsUrl = `${protocol}//${apiHost}/api/v1/transcription/ws/${sessionId}`;
        const ws = new WebSocket(wsUrl);
        channel.ws = ws;

        // Single ws.onopen — handles state AND promise in one handler (PART 1 fix)
        let openResolve: (() => void) | null = null;
        ws.onopen = () => {
          if (channel.stopRequested) return;
          channel.socketOpened = true;
          channel.state = "socket_open";
          channel.deepgramState = "connected";
          setState(s => ({ ...s, isConnected: true }));
          setChannelHealth(role, "connecting");
          logDiag(channel, "socket open");
          if (openResolve) openResolve();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "partial" || data.type === "final") {
              channel.interimCount++;
              channel.lastTranscriptAt = Date.now();
              if (data.type === "final") {
                channel.finalCount++;
                channel.deepgramState = "streaming";
                setChannelHealth(role, "streaming");
              }
              const seg: TranscriptSegment = {
                id: data.utterance_id || `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                speaker: speakerLabel,
                text: data.text || "",
                start: data.start || 0,
                end: data.end || 0,
                confidence: data.confidence || 0,
                isFinal: data.type === "final",
                words: data.words || [],
                utteranceNumber: data.utterance_number,
                sourceRole: role,
              };
              upsertSegment(seg);
              if (data.type === "final") {
                logDiag(channel, `final: "${(data.text || "").slice(0, 50)}"`);
              }
            } else if (data.type === "error") {
              channel.errorCode = data.error;
              setState(s => ({ ...s, error: `${role}: ${data.error}` }));
            }
          } catch { /* ignore */ }
        };

        ws.onerror = () => {
          channel.errorCode = "ws_error";
          channel.state = "failed";
          setChannelHealth(role, "failed");
          setState(s => ({ ...s, error: `${role} WebSocket error` }));
        };

        ws.onclose = () => {
          channel.socketOpened = false;
          channel.deepgramState = "disconnected";
          if (!channel.stopRequested) {
            channel.state = "failed";
            setChannelHealth(role, "failed");
          }
          setState(s => ({
            ...s,
            isConnected: Array.from(channelsRef.current.values()).some(c => c.socketOpened),
            isStreaming: Array.from(channelsRef.current.values()).some(c => c.state === "streaming"),
            activeSessions: s.activeSessions.filter(r => r !== role),
          }));
          channelsRef.current.delete(role);
        };

        // Wait for socket open with timeout
        await new Promise<void>((resolve, reject) => {
          if (ws.readyState === WebSocket.OPEN) { resolve(); return; }
          openResolve = resolve;
          const timeout = setTimeout(() => {
            channel.errorCode = "ws_timeout";
            reject(new Error(`${role} WebSocket timeout`));
          }, 10000);
          const orig = openResolve;
          openResolve = () => { clearTimeout(timeout); orig?.(); };
        });

        if (channel.stopRequested) return;

        // ── 3. Start PCM processor ──
        channel.state = "processor_starting";
        channel.processorStarted = true;
        const processor = new PcmAudioProcessor(role);
        channel.processor = processor;

        // Wire watchdog — if the audio graph never starts rendering, fail the channel
        processor.setFailedCallback((failedRole, reason) => {
          channel.errorCode = reason;
          channel.state = "failed";
          setChannelHealth(failedRole, "failed");
          setState(s => ({
            ...s,
            error: `[${failedRole}] ${reason}: Audio processor did not start rendering within 1s`,
            activeSessions: s.activeSessions.filter(r => r !== failedRole),
          }));
        });

        processor.start(audioStream, (chunk) => {
          if (channel.stopRequested) return;
          if (channel.ws?.readyState === WebSocket.OPEN) {
            channel.chunkCount++;
            channel.bytesSent += chunk.bytes.length;
            channel.lastAudioAt = Date.now();

            // Every 100 chunks, log + update diagnostics
            if (channel.chunkCount % 100 === 0) {
              const diag = processor.getDiagnostics();
              setState(s => ({
                ...s,
                [role === "agent" ? "agentDiagnostics" : "prospectDiagnostics"]: diag,
              }));
              logDiag(channel, `chunk #${channel.chunkCount} rms=${diag.rmsLevel.toFixed(4)} peak=${diag.peakLevel.toFixed(3)}`);
            }

            let binary = "";
            for (let i = 0; i < chunk.bytes.length; i++) {
              binary += String.fromCharCode(chunk.bytes[i]);
            }
            channel.ws.send(JSON.stringify({ type: "audio", data: btoa(binary) }));
          }
        });

        channel.state = "streaming";
        setChannelHealth(role, "streaming");
        logDiag(channel, "processor started, streaming");
        channelsRef.current.set(role, channel);

      } catch (e) {
        channel.state = "failed";
        channel.errorCode = e instanceof Error ? e.message : "startup_failed";
        setChannelHealth(role, "failed");
        setState(s => ({
          ...s,
          error: e instanceof Error ? e.message : `Failed to start ${role}`,
          activeSessions: s.activeSessions.filter(r => r !== role),
        }));
        channelsRef.current.delete(role);
      }
    })();

    channel.startPromise = startPromise;
    channelsRef.current.set(role, channel);
    await startPromise;
  }, [cleanupChannel, cleanupAll, setChannelHealth, logDiag, upsertSegment]);

  // ── Stop ──

  const stopAll = useCallback(async () => {
    const sessionIds: string[] = [];
    for (const ch of channelsRef.current.values()) {
      sessionIds.push(ch.sessionId);
      cleanupChannel(ch);
    }
    segmentsRef.current = [];
    fullTextRef.current = "";
    activeCallIdRef.current = null;
    setState(INITIAL_STATE);

    for (const sid of sessionIds) {
      try {
        await fetch(`/api/transcription/${sid}/stop`, { method: "POST" });
      } catch { /* best effort */ }
    }
  }, [cleanupChannel]);

  const stopSession = useCallback(async (role: AudioSourceRole) => {
    const ch = channelsRef.current.get(role);
    if (!ch) return;
    try { await fetch(`/api/transcription/${ch.sessionId}/stop`, { method: "POST" }); } catch { /* */ }
    cleanupChannel(ch);
    setState(s => ({
      ...s,
      activeSessions: s.activeSessions.filter(r => r !== role),
      isConnected: Array.from(channelsRef.current.values()).some(c => c.socketOpened && c.role !== role),
      isStreaming: Array.from(channelsRef.current.values()).some(c => c.state === "streaming" && c.role !== role),
    }));
    setChannelHealth(role, "stopped");
  }, [cleanupChannel, setChannelHealth]);

  return {
    ...state,
    startSession,
    stopAll,
    stopSession,
    // Backward compat aliases
    startTranscription: startSession,
    stopTranscription: stopAll,
  };
}
