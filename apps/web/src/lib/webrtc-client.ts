"use client";

/**
 * Telnyx WebRTC Client — singleton wrapper around @telnyx/webrtc SDK.
 *
 * Architecture:
 *   getUserMedia → TelnyxRTC client → call.newCall() → PeerConnection → audio
 *
 * This module owns:
 *   - SDK client lifecycle (connect, disconnect)
 *   - Microphone stream acquisition & release
 *   - Outbound call creation with media attachment
 *   - Event logging for debugging
 *
 * The TelephonyContext consumes this via hooks — never imports SDK directly.
 */

import type { Call } from "@telnyx/webrtc";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let TelnyxRTC: any = null;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function loadSdk(): Promise<any> {
  if (TelnyxRTC) return TelnyxRTC;
  const mod = await import("@telnyx/webrtc");
  TelnyxRTC = mod.default || mod.TelnyxRTC;
  return TelnyxRTC;
}

export type WrtcState =
  | "uninitialized"
  | "loading"
  | "connected"
  | "registered"
  | "failed";

export type WrtcCallState =
  | "idle"
  | "dialing"
  | "ringing"
  | "answered"
  | "active"
  | "held"
  | "hangup"
  | "destroy"
  | "error";

export interface WrtcDiagnostics {
  sdkLoaded: boolean;
  clientState: WrtcState;
  callState: WrtcCallState;
  direction: "outbound" | "inbound" | "";
  micGranted: boolean;
  localTrack: boolean;
  remoteTrack: boolean;
  peerState: string;
  iceState: string;
  packetsSent: number;
  packetsReceived: number;
  bytesSent: number;
  bytesReceived: number;
  codec: string;
  selectedIcePair: string;
  muted: boolean;
  held: boolean;
}

export interface IncomingCallInfo {
  callId: string;
  callerNumber: string;
  callerName: string;
  state: "ringing" | "answered" | "ended" | "declined";
}

// ── Singleton state ──

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _client: any = null;
let _micStream: MediaStream | null = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _activeCall: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _incomingCall: any = null;
let _remoteAudio: HTMLAudioElement | null = null;
const _diagnostics: WrtcDiagnostics = {
  sdkLoaded: false,
  clientState: "uninitialized",
  callState: "idle",
  direction: "",
  micGranted: false,
  localTrack: false,
  remoteTrack: false,
  peerState: "new",
  iceState: "new",
  packetsSent: 0,
  packetsReceived: 0,
  bytesSent: 0,
  bytesReceived: 0,
  codec: "",
  selectedIcePair: "",
  muted: false,
  held: false,
};
let _onDiagnosticsChange: ((d: WrtcDiagnostics) => void) | null = null;
let _onCallStateChange: ((state: WrtcCallState, callId?: string) => void) | null = null;
let _onIncomingCall: ((info: IncomingCallInfo) => void) | null = null;
let _onIncomingCallEnded: (() => void) | null = null;
let _previousCallState: string | null = null;
let _tokenRefreshCallback: (() => Promise<string>) | null = null;
let _reconnectTimer: ReturnType<typeof setTimeout> | null = null;

export function getDiagnostics(): WrtcDiagnostics {
  return { ..._diagnostics };
}

export function onDiagnosticsChange(cb: (d: WrtcDiagnostics) => void) {
  _onDiagnosticsChange = cb;
}

export function onCallStateChange(cb: (state: WrtcCallState, callId?: string) => void) {
  _onCallStateChange = cb;
}

export function onIncomingCall(cb: (info: IncomingCallInfo) => void) {
  _onIncomingCall = cb;
}

export function onIncomingCallEnded(cb: () => void) {
  _onIncomingCallEnded = cb;
}

function updateDiagnostics(partial: Partial<WrtcDiagnostics>) {
  Object.assign(_diagnostics, partial);
  _onDiagnosticsChange?.({ ..._diagnostics });
}

/**
 * Map Telnyx SDK call.state string to our WrtcCallState enum.
 * SDK states: new, requesting, trying, ringing, answering, early, active, held, hangup, destroy, purge
 */
function mapSdkState(s: string | null | undefined): WrtcCallState {
  switch (s) {
    case "requesting":
    case "trying":
      return "dialing";
    case "ringing":
    case "early":
      return "ringing";
    case "answering":
      return "ringing";
    case "active":
      return "active";
    case "held":
      return "held";
    case "hangup":
      return "hangup";
    case "destroy":
    case "purge":
      return "destroy";
    default:
      return "idle";
  }
}

// ── Microphone ──

export async function acquireMicrophone(): Promise<MediaStream> {
  if (_micStream) {
    const tracks = _micStream.getAudioTracks();
    if (tracks.length > 0 && tracks[0].readyState === "live") {
      updateDiagnostics({ micGranted: true, localTrack: true });
      return _micStream;
    }
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  _micStream = stream;
  updateDiagnostics({ micGranted: true, localTrack: true });
  return stream;
}

export function releaseMicrophone() {
  if (_micStream) {
    _micStream.getTracks().forEach((t) => t.stop());
    _micStream = null;
  }
  updateDiagnostics({ micGranted: false, localTrack: false });
}

export function getMicrophoneStream(): MediaStream | null {
  return _micStream;
}

export function getRemoteAudioElement(): HTMLAudioElement | null {
  return _remoteAudio;
}

export function getRemoteStream(): MediaStream | null {
  // Try to get remote stream from active call
  if (_activeCall?.remoteStream) return _activeCall.remoteStream;
  // Fallback: get from audio element
  if (_remoteAudio?.srcObject instanceof MediaStream) return _remoteAudio.srcObject;
  // Fallback: get from peer connection receivers
  try {
    const pc = _activeCall?.peerConnection;
    if (pc) {
      const receivers = pc.getReceivers?.() || [];
      for (const r of receivers) {
        if (r.track?.kind === "audio" && r.track.readyState === "live") {
          return new MediaStream([r.track]);
        }
      }
    }
  } catch { /* not available */ }
  return null;
}

// ── Remote audio element ──

function ensureRemoteAudio(): HTMLAudioElement {
  if (_remoteAudio) return _remoteAudio;
  let el = document.getElementById("pns-remote-audio") as HTMLAudioElement;
  if (!el) {
    el = document.createElement("audio");
    el.id = "pns-remote-audio";
    el.autoplay = true;
    el.style.display = "none";
    document.body.appendChild(el);
  }
  _remoteAudio = el;
  return el;
}

// ── Client initialization ──

export function setTokenRefreshCallback(cb: () => Promise<string>) {
  _tokenRefreshCallback = cb;
}

export async function initWebRTC(login: string, password: string): Promise<void> {
  if (_client && _diagnostics.clientState === "connected") {
    return;
  }

  updateDiagnostics({ clientState: "loading" });

  try {
    const SDK = await loadSdk();
    updateDiagnostics({ sdkLoaded: true });

    _client = new SDK({
      login,
      password,
      debug: false,  // Sprint 47.4: Never log SIP credentials to console
    });

    // Wire up client lifecycle events
    _client.on("telnyx.ready", () => {
      updateDiagnostics({ clientState: "connected" });
    });

    _client.on("telnyx.socket.open", () => {
      updateDiagnostics({ clientState: "connected" });
    });

    _client.on("telnyx.socket.close", () => {
      updateDiagnostics({ clientState: "uninitialized" });
      _scheduleReconnect();
    });

    _client.on("telnyx.error", () => {
      updateDiagnostics({ clientState: "failed" });
      _scheduleReconnect();
    });

    // ── Call state tracking via telnyx.notification ──
    _client.on("telnyx.notification", (notification: Record<string, unknown>) => {
      if (notification.type !== "callUpdate") return;

      const call = notification.call as Record<string, unknown>;
      if (!call) return;

      const callId = call.id as string;
      const newState = call.state as string;
      const direction = call.direction as string;

      // Inbound call: different call ID than our active outbound call
      if (direction === "incoming" || (!_activeCall && callId)) {
        if (!_incomingCall && newState !== "hangup" && newState !== "destroy" && newState !== "purge") {
          _incomingCall = call;
          const callerNumber = (call.caller_id_number || call.callerNumber || call.caller_number || "Unknown") as string;
          const callerName = (call.caller_id_name || call.callerName || call.caller_name || callerNumber) as string;
          updateDiagnostics({ callState: "ringing", direction: "inbound" });
          _onIncomingCall?.({
            callId: callId,
            callerNumber,
            callerName,
            state: "ringing",
          });
        }
        // Track state changes for the incoming call
        if (_incomingCall && callId === _incomingCall.id) {
          if (newState === "active") {
            updateDiagnostics({ callState: "active" });
          } else if (newState === "hangup" || newState === "destroy" || newState === "purge") {
            cleanupIncomingCall();
          }
        }
        return;
      }

      if (callId !== _activeCall?.id) return;

      if (newState === _previousCallState) return;
      _previousCallState = newState;

      // Track PeerConnection & ICE from call object
      _extractPeerDiagnostics(call);

      const mapped = mapSdkState(newState);

      switch (mapped) {
        case "ringing":
          updateDiagnostics({ callState: "ringing" });
          _onCallStateChange?.("ringing", call.id as string);
          break;
        case "active":
          updateDiagnostics({ callState: "active" });
          _onCallStateChange?.("active", call.id as string);
          break;
        case "held":
          updateDiagnostics({ callState: "held" });
          _onCallStateChange?.("held", call.id as string);
          break;
        case "hangup":
        case "destroy":
          updateDiagnostics({ callState: mapped });
          _onCallStateChange?.(mapped, call.id as string);
          cleanupCall();
          break;
        default:
          break;
      }
    });

    // ── Stats via telnyx.stats.frame ──
    _client.on("telnyx.stats.frame", (stats: Array<Record<string, unknown>>) => {
      if (!_activeCall || !stats?.length) return;
      let packetsSent = 0;
      let packetsReceived = 0;
      let bytesSent = 0;
      let bytesReceived = 0;
      let codec = "";
      let selectedIcePair = "";
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      stats.forEach((r: any) => {
        if (r.type === "outbound-rtp" && r.kind === "audio") {
          packetsSent = r.packetsSent || 0;
          bytesSent = r.bytesSent || 0;
          if (r.codecId) codec = r.codecId;
        }
        if (r.type === "inbound-rtp" && r.kind === "audio") {
          packetsReceived = r.packetsReceived || 0;
          bytesReceived = r.bytesReceived || 0;
        }
        if (r.type === "candidate-pair" && r.state === "succeeded") {
          selectedIcePair = `local:${r.localCandidateId} remote:${r.remoteCandidateId} (${r.nominated ? "nominated" : "not nominated"})`;
        }
        // Resolve codec name from codec stats
        if (r.type === "codec" && r.mimeType) {
          codec = r.mimeType;
        }
      });
      const patch: Partial<WrtcDiagnostics> = { packetsSent, packetsReceived, bytesSent, bytesReceived };
      if (codec) patch.codec = codec;
      if (selectedIcePair) patch.selectedIcePair = selectedIcePair;
      updateDiagnostics(patch);
    });

    _client.connect();

    // Wait for ready
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("Connection timeout")), 10000);
      _client.on("telnyx.ready", () => {
        clearTimeout(timeout);
        resolve();
      });
    });

    // Connected successfully
  } catch (e) {
    // Init failed — diagnostics already updated
    updateDiagnostics({ clientState: "failed" });
    throw e;
  }
}

// ── Reconnect ──

function _scheduleReconnect() {
  if (_reconnectTimer) return;
  _reconnectTimer = setTimeout(async () => {
    _reconnectTimer = null;
    if (!_tokenRefreshCallback) {
      return;
    }
    try {
      const newToken = await _tokenRefreshCallback();
      // Decode base64 token into login:password for SDK
      const decoded = atob(newToken);
      const colonIdx = decoded.indexOf(":");
      if (colonIdx === -1) throw new Error("Invalid token format");
      const login = decoded.slice(0, colonIdx);
      const password = decoded.slice(colonIdx + 1);
      await initWebRTC(login, password);
    } catch {
      // Try again in 10s
      _reconnectTimer = setTimeout(() => _scheduleReconnect(), 10000);
    }
  }, 3000);
}

// ── PeerConnection / ICE diagnostics ──

function _extractPeerDiagnostics(call: Record<string, unknown>) {
  try {
    // Try to access the peer connection via the call's internal state
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = call as any;
    if (c.peer?.instance) {
      const pc = c.peer.instance as RTCPeerConnection;
      updateDiagnostics({
        peerState: pc.connectionState || "unknown",
        iceState: pc.iceConnectionState || "unknown",
      });
    }
  } catch {
    // PeerConnection not accessible yet
  }
}

// ── Outbound call ──

export async function makeCall(
  destination: string,
  callerNumber: string,
  callerName: string,
): Promise<void> {
  if (!_client || _diagnostics.clientState !== "connected") {
    throw new Error("WebRTC client not connected");
  }

  updateDiagnostics({ callState: "dialing" });
  _onCallStateChange?.("dialing");
  _previousCallState = null;

  try {
    const micStream = await acquireMicrophone();
    const remoteAudio = ensureRemoteAudio();

    const call: Call = _client.newCall({
      destinationNumber: destination,
      callerNumber: callerNumber,
      callerName: callerName,
      localStream: micStream,
      remoteElement: remoteAudio,
      audio: true,
      debug: false,  // Sprint 47.4: Never log SIP credentials
    });

    _activeCall = call;

  } catch (e) {
    updateDiagnostics({ callState: "error" });
    _onCallStateChange?.("error");
    throw e;
  }
}

// ── Hangup ──

export async function hangupCall(): Promise<void> {
  if (_activeCall) {
    try {
      _activeCall.hangup();
    } catch {
      // Hangup failed — cleanup anyway
    }
  }
  cleanupCall();
}

// ── Mute / Unmute ──

export function muteCall(): void {
  if (!_activeCall) return;
  try {
    _activeCall.muteAudio();
    updateDiagnostics({ muted: true });
  } catch {
    // Mute failed — state unchanged
  }
}

export function unmuteCall(): void {
  if (!_activeCall) return;
  try {
    _activeCall.unmuteAudio();
    updateDiagnostics({ muted: false });
  } catch {
    // Unmute failed — state unchanged
  }
}

// ── Hold / Resume ──

export function holdCall(): void {
  if (!_activeCall) return;
  try {
    _activeCall.hold();
    updateDiagnostics({ held: true });
  } catch {
    // Hold failed — state unchanged
  }
}

export function resumeCall(): void {
  if (!_activeCall) return;
  try {
    _activeCall.unhold();
    updateDiagnostics({ held: false });
  } catch {
    // Resume failed — state unchanged
  }
}

// ── Volume control ──

export function setVolume(volume: number): void {
  const el = _remoteAudio || (document.getElementById("pns-remote-audio") as HTMLAudioElement);
  if (el) {
    el.volume = Math.max(0, Math.min(1, volume));
  }
}

export function getVolume(): number {
  const el = _remoteAudio || (document.getElementById("pns-remote-audio") as HTMLAudioElement);
  return el?.volume ?? 1;
}

// ── Speaker device switching ──

export async function setSpeaker(deviceId: string): Promise<void> {
  const el = _remoteAudio || (document.getElementById("pns-remote-audio") as HTMLAudioElement);
  if (!el) return;
  if ("setSinkId" in el && typeof (el as HTMLAudioElement & { setSinkId: (id: string) => Promise<void> }).setSinkId === "function") {
    try {
      await (el as HTMLAudioElement & { setSinkId: (id: string) => Promise<void> }).setSinkId(deviceId);
    } catch {
      // setSinkId failed — speaker unchanged
    }
  }
}

// ── DTMF ──

export function sendDtmf(digit: string): void {
  if (!_activeCall) return;
  try {
    _activeCall.dtmf(digit);
  } catch {
    // DTMF failed
  }
}

function cleanupCall() {
  _activeCall = null;
  _previousCallState = null;
  releaseMicrophone();
  updateDiagnostics({
    callState: "idle",
    direction: "",
    remoteTrack: false,
    packetsSent: 0,
    packetsReceived: 0,
    bytesSent: 0,
    bytesReceived: 0,
    codec: "",
    selectedIcePair: "",
    muted: false,
    held: false,
  });
}

// ── Inbound call handling ──

export async function answerIncomingCall(): Promise<void> {
  if (!_incomingCall) return;
  try {
    const micStream = await acquireMicrophone();
    const remoteAudio = ensureRemoteAudio();
    _incomingCall.answer({
      localStream: micStream,
      remoteElement: remoteAudio,
    });
    _activeCall = _incomingCall;
    _incomingCall = null;
    updateDiagnostics({ callState: "active", direction: "inbound", localTrack: true });
    _onCallStateChange?.("active");
  } catch (e) {
    updateDiagnostics({ callState: "error" });
    throw e;
  }
}

export async function declineIncomingCall(): Promise<void> {
  if (!_incomingCall) return;
  try {
    _incomingCall.hangup();
  } catch {
    // cleanup anyway
  }
  cleanupIncomingCall();
}

function cleanupIncomingCall() {
  _incomingCall = null;
  updateDiagnostics({ callState: "idle", direction: "" });
  _onIncomingCallEnded?.();
}

// ── Disconnect ──

export function disconnect() {
  if (_reconnectTimer) {
    clearTimeout(_reconnectTimer);
    _reconnectTimer = null;
  }
  hangupCall();
  if (_client) {
    try { _client.disconnect(); } catch { /* cleanup */ }
    _client = null;
  }
  updateDiagnostics({ clientState: "uninitialized" });
}
