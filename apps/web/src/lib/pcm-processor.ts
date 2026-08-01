/**
 * PcmAudioProcessor — Resamples browser audio to 16kHz mono PCM16 little-endian.
 * Sprint 47.3 — Added RMS/peak/silence diagnostics per PART 3-4.
 *
 * Architecture:
 *   MediaStream → AudioContext (native rate) → ScriptProcessor → Resampler → PCM16 → callback
 *
 * Never breaks the playback path. Operates as a passive branch.
 */

export type AudioSourceRole = "agent" | "prospect";

export type PcmChunk = {
  role: AudioSourceRole;
  bytes: Uint8Array;
  timestamp: number;
};

export type PcmDiagnostics = {
  role: AudioSourceRole;
  trackId: string;
  trackLabel: string;
  trackState: string;
  inputSampleRate: number;
  outputSampleRate: number;
  channels: number;
  chunksSent: number;
  bytesSent: number;
  active: boolean;
  lastChunkAt: number;
  rmsLevel: number;
  peakLevel: number;
  zeroSamplePct: number;
  clippingPct: number;
  expectedChunkBytes: number;
  actualChunkBytes: number;
  chunkDurationMs: number;
  bufferSize: number;
  silent: boolean;
  activeChunks: number;
  silentChunks: number;
  rmsMin: number;
  rmsMax: number;
};

const RMS_SILENCE_FLOOR = 0.005;
const SILENCE_CONSECUTIVE_THRESHOLD = 3;

export class PcmAudioProcessor {
  private _role: AudioSourceRole;
  private _audioCtx: AudioContext | null = null;
  private _source: MediaStreamAudioSourceNode | null = null;
  private _processor: ScriptProcessorNode | null = null;
  private _silentGain: GainNode | null = null;
  private _stream: MediaStream | null = null;
  private _clonedTrack: MediaStreamTrack | null = null;
  private _callback: ((chunk: PcmChunk) => void) | null = null;
  private _startTime = 0;
  private _consecutiveSilent = 0;
  private _diag: PcmDiagnostics;
  private _callbackCount = 0;
  private _watchdogTimer: ReturnType<typeof setTimeout> | null = null;
  private _onFailed?: (role: AudioSourceRole, reason: string) => void;

  constructor(role: AudioSourceRole) {
    this._role = role;
    this._diag = {
      role,
      trackId: "", trackLabel: "", trackState: "",
      inputSampleRate: 0, outputSampleRate: 16000, channels: 1,
      chunksSent: 0, bytesSent: 0, active: false, lastChunkAt: 0,
      rmsLevel: 0, peakLevel: 0, zeroSamplePct: 0, clippingPct: 0,
      expectedChunkBytes: 0, actualChunkBytes: 0, chunkDurationMs: 0, bufferSize: 0,
      silent: true, activeChunks: 0, silentChunks: 0, rmsMin: 1, rmsMax: 0,
    };
  }

  setFailedCallback(cb: (role: AudioSourceRole, reason: string) => void): void {
    this._onFailed = cb;
  }

  start(stream: MediaStream, onChunk: (chunk: PcmChunk) => void): void {
    if (this._diag.active) return;
    this._stream = stream;
    this._callback = onChunk;

    const track = stream.getAudioTracks()[0];
    if (!track) {
      console.warn(`[PcmProcessor:${this._role}] No audio track in stream`);
      return;
    }

    const settings = track.getSettings();
    const nativeRate = settings.sampleRate || 44100;
    this._diag.trackId = track.id;
    this._diag.trackLabel = track.label;
    this._diag.trackState = track.readyState;
    this._diag.inputSampleRate = nativeRate;

    console.log(
      `[PcmProcessor:${this._role}] Track — id=${track.id} label="${track.label}" state=${track.readyState} rate=${nativeRate}Hz`
    );

    this._audioCtx = new AudioContext({ sampleRate: nativeRate });
    console.log(`[PcmProcessor:${this._role}] AudioContext created — state=${this._audioCtx.state} sampleRate=${this._audioCtx.sampleRate}`);

    // Clone the audio track — the original track is owned by WebRTC's RTCPeerConnection
    // and cannot be read by a MediaStreamAudioSourceNode simultaneously.
    // A cloned track is an independent copy that the AudioContext can process freely.
    this._clonedTrack = track.clone();
    const clonedStream = new MediaStream([this._clonedTrack]);
    console.log(`[PcmProcessor:${this._role}] Track cloned — original=${track.id} cloned=${this._clonedTrack.id}`);

    this._source = this._audioCtx.createMediaStreamSource(clonedStream);

    const ratio = nativeRate / 16000;
    const targetSamples = 640;
    const bufferSize = [256, 512, 1024, 2048, 4096, 8192, 16384]
      .find(s => s >= targetSamples * ratio) || 16384;
    this._diag.bufferSize = bufferSize;
    this._diag.chunkDurationMs = Math.round((bufferSize / nativeRate) * 1000);
    this._diag.expectedChunkBytes = Math.round(bufferSize / ratio) * 2;

    this._processor = this._audioCtx.createScriptProcessor(bufferSize, 1, 1);

    // Silent gain node — required for ScriptProcessorNode to fire onaudioprocess.
    // A ScriptProcessorNode must be connected to an active output graph
    // (terminating at AudioContext.destination), otherwise the browser will
    // never schedule its callback.  Gain is zero so no audible playback.
    this._silentGain = this._audioCtx.createGain();
    this._silentGain.gain.value = 0;

    // Graph: source → processor → silentGain (0) → destination
    this._source.connect(this._processor);
    this._processor.connect(this._silentGain);
    this._silentGain.connect(this._audioCtx.destination);

    console.log(
      `[PcmProcessor:${this._role}] graph connected: ` +
      `source → processor → silentGain → destination`
    );

    this._diag.active = true;
    this._startTime = Date.now();
    this._consecutiveSilent = 0;
    this._callbackCount = 0;
    this._diag.silent = true;
    this._diag.rmsMin = 1;
    this._diag.rmsMax = 0;

    // Set up onaudioprocess handler
    this._processor.onaudioprocess = (e: AudioProcessingEvent) => {
      if (!this._callback) return;
      this._callbackCount++;

      const input = e.inputBuffer.getChannelData(0);
      const resampled = this._resampleLinear(input, nativeRate, 16000);
      const pcm = new Int16Array(resampled.length);

      let sumSq = 0, peak = 0, zeroCount = 0, clipCount = 0;
      for (let i = 0; i < resampled.length; i++) {
        const s = resampled[i];
        const clamped = Math.max(-1, Math.min(1, s));
        pcm[i] = clamped < 0 ? Math.round(clamped * 32768) : Math.round(clamped * 32767);
        sumSq += clamped * clamped;
        const absV = Math.abs(clamped);
        if (absV > peak) peak = absV;
        if (absV < 1e-6) zeroCount++;
        if (absV >= 0.999) clipCount++;
      }

      const rms = Math.sqrt(sumSq / Math.max(1, resampled.length));
      this._diag.rmsLevel = rms;
      this._diag.peakLevel = peak;
      this._diag.zeroSamplePct = (zeroCount / Math.max(1, resampled.length)) * 100;
      this._diag.clippingPct = (clipCount / Math.max(1, resampled.length)) * 100;
      this._diag.actualChunkBytes = pcm.byteLength;
      if (rms < this._diag.rmsMin) this._diag.rmsMin = rms;
      if (rms > this._diag.rmsMax) this._diag.rmsMax = rms;

      if (rms < RMS_SILENCE_FLOOR) {
        this._consecutiveSilent++;
        this._diag.silentChunks++;
        if (this._consecutiveSilent >= SILENCE_CONSECUTIVE_THRESHOLD) this._diag.silent = true;
      } else {
        this._consecutiveSilent = 0;
        this._diag.silent = false;
        this._diag.activeChunks++;
      }

      if (pcm.byteLength % 2 !== 0 || pcm.byteLength === 0) {
        console.error(`[PcmProcessor:${this._role}] PCM_FORMAT_INVALID: byteLength=${pcm.byteLength}`);
      }

      this._diag.chunksSent++;
      this._diag.bytesSent += pcm.byteLength;
      this._diag.lastChunkAt = Date.now();

      // First callback — log unconditionally with full diagnostics
      if (this._callbackCount === 1) {
        console.log(
          `[PcmProcessor:${this._role}] onaudioprocess fired ` +
          `inputFrames=${input.length} inputRate=${nativeRate}Hz ` +
          `outputSamples=${resampled.length} outputBytes=${pcm.byteLength} ` +
          `rms=${rms.toFixed(4)} peak=${peak.toFixed(3)} ` +
          `zeroPct=${this._diag.zeroSamplePct.toFixed(1)}`
        );
      } else if (this._diag.chunksSent % 50 === 0) {
        console.log(
          `[PcmProcessor:${this._role}] chunk=${this._diag.chunksSent} rms=${rms.toFixed(4)} peak=${peak.toFixed(3)} ` +
          `zeroPct=${this._diag.zeroSamplePct.toFixed(1)} silent=${this._diag.silent} bytes=${pcm.byteLength}`
        );
      }

      this._callback({
        role: this._role,
        bytes: new Uint8Array(pcm.buffer),
        timestamp: Date.now() - this._startTime,
      });
    };

    console.log(
      `[PcmProcessor:${this._role}] Started — input=${nativeRate}Hz buffer=${bufferSize} ` +
      `chunkMs=${this._diag.chunkDurationMs}ms expectedBytes=${this._diag.expectedChunkBytes} ` +
      `ctxState=${this._audioCtx?.state}`
    );

    // Force resume — in Electron/Chromium, contexts created outside user gesture may be suspended
    this._audioCtx.resume().then(() => {
      console.log(`[PcmProcessor:${this._role}] Resume complete — ctxState=${this._audioCtx?.state}`);
    }).catch((err) => {
      console.error(`[PcmProcessor:${this._role}] Resume failed:`, err);
    });

    // ── Startup watchdog: if no callback after 1s, the graph isn't rendering ──
    this._watchdogTimer = setTimeout(() => {
      if (this._callbackCount === 0 && this._diag.active) {
        const reason = "AUDIO_PROCESSOR_NOT_RENDERING";
        console.error(
          `[PcmProcessor:${this._role}] ${reason} — ` +
          `callbackCount=${this._callbackCount} ` +
          `ctxState=${this._audioCtx?.state} ` +
          `trackState=${track.readyState} ` +
          `trackEnabled=${track.enabled} ` +
          `trackMuted=${track.muted} ` +
          `originalTrackId=${track.id} ` +
          `cloneTrackId=${this._clonedTrack?.id}`
        );
        this._onFailed?.(this._role, reason);
      }
    }, 1000);
  }

  stop(): void {
    this._diag.active = false;

    // Clear watchdog
    if (this._watchdogTimer) { clearTimeout(this._watchdogTimer); this._watchdogTimer = null; }

    // Disconnect graph in order: source → processor → silentGain
    if (this._source) { try { this._source.disconnect(); } catch { /* */ } this._source = null; }
    if (this._processor) { try { this._processor.disconnect(); } catch { /* */ } this._processor = null; }
    if (this._silentGain) { try { this._silentGain.disconnect(); } catch { /* */ } this._silentGain = null; }

    // Stop cloned track (NOT the original Telnyx-owned track)
    if (this._clonedTrack) { this._clonedTrack.stop(); this._clonedTrack = null; }

    // Close AudioContext
    if (this._audioCtx && this._audioCtx.state !== "closed") {
      this._audioCtx.close().catch(() => {});
      this._audioCtx = null;
    }
    this._callback = null;
    this._stream = null;

    console.log(
      `[PcmProcessor:${this._role}] Stopped — chunks=${this._diag.chunksSent} bytes=${this._diag.bytesSent} ` +
      `rms=[${this._diag.rmsMin.toFixed(4)}-${this._diag.rmsMax.toFixed(4)}] ` +
      `active=${this._diag.activeChunks} silent=${this._diag.silentChunks} ` +
      `callbacks=${this._callbackCount}`
    );
  }

  getDiagnostics(): PcmDiagnostics { return { ...this._diag }; }

  private _resampleLinear(input: Float32Array, srcRate: number, dstRate: number): Float32Array {
    if (srcRate === dstRate) return new Float32Array(input);
    const ratio = srcRate / dstRate;
    const outLen = Math.floor(input.length / ratio);
    const out = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      const srcIdx = i * ratio;
      const srcFloor = Math.floor(srcIdx);
      const frac = srcIdx - srcFloor;
      const a = input[srcFloor] || 0;
      const b = input[Math.min(srcFloor + 1, input.length - 1)] || 0;
      out[i] = a + (b - a) * frac;
    }
    return out;
  }
}
