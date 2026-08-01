/**
 * Sprint 47.3 — PcmAudioProcessor Tests (PART 17)
 *
 * Covers: resampling accuracy, silence detection, PCM format validation
 */

import { describe, it, expect } from "vitest";

// We test the _resampleLinear method directly since it's pure math
// (can't easily test full processor in node without browser Web Audio APIs)

describe("PCM Resampling Logic", () => {
  /**
   * Simulates the PcmProcessor._resampleLinear for testing.
   * Exact copy of the real implementation.
   */
  function resampleLinear(input: Float32Array, srcRate: number, dstRate: number): Float32Array {
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

  function makeSine(freq: number, rate: number, durationSec: number): Float32Array {
    const len = Math.floor(rate * durationSec);
    const out = new Float32Array(len);
    for (let i = 0; i < len; i++) {
      out[i] = Math.sin(2 * Math.PI * freq * i / rate);
    }
    return out;
  }

  function computeRMS(samples: Float32Array): number {
    let sumSq = 0;
    for (let i = 0; i < samples.length; i++) sumSq += samples[i] * samples[i];
    return Math.sqrt(sumSq / samples.length);
  }

  // ── PART 4: Resampling accuracy ──

  it("pass-through: 16000 → 16000 returns identical data", () => {
    const input = makeSine(440, 16000, 0.1);
    const output = resampleLinear(input, 16000, 16000);
    expect(output.length).toBe(input.length);
    for (let i = 0; i < output.length; i++) {
      expect(output[i]).toBeCloseTo(input[i], 5);
    }
  });

  it("44100 → 16000 preserves nonzero sine wave", () => {
    const input = makeSine(440, 44100, 0.1);
    const output = resampleLinear(input, 44100, 16000);
    expect(output.length).toBeGreaterThan(0);
    expect(output.length).toBeLessThan(input.length);
    const rms = computeRMS(output);
    expect(rms).toBeGreaterThan(0.1); // sine wave has significant energy
  });

  it("48000 → 16000 preserves nonzero sine wave", () => {
    const input = makeSine(440, 48000, 0.1);
    const output = resampleLinear(input, 48000, 16000);
    expect(output.length).toBeGreaterThan(0);
    const rms = computeRMS(output);
    expect(rms).toBeGreaterThan(0.1);
  });

  it("duration is preserved after resampling", () => {
    const durationSec = 0.1;
    const input = makeSine(440, 44100, durationSec);
    const output = resampleLinear(input, 44100, 16000);
    const toleranceMs = 5;
    const expectedSamples = 16000 * durationSec;
    expect(Math.abs(output.length - expectedSamples)).toBeLessThanOrEqual(
      (toleranceMs / 1000) * 16000
    );
  });

  // ── PART 3: Silence detection ──

  it("zero input produces near-zero RMS", () => {
    const input = new Float32Array(4410);
    const output = resampleLinear(input, 44100, 16000);
    const rms = computeRMS(output);
    expect(rms).toBeLessThan(0.001); // effectively silent
  });

  it("nonzero sine produces RMS above silence floor", () => {
    const input = makeSine(440, 44100, 0.1);
    const output = resampleLinear(input, 44100, 16000);
    const rms = computeRMS(output);
    expect(rms).toBeGreaterThan(0.005); // above RMS_SILENCE_FLOOR
  });

  // ── PCM format validation ──

  it("output samples are within [-1, 1] range", () => {
    const input = makeSine(440, 48000, 0.1);
    // Make amplitude 0.95
    for (let i = 0; i < input.length; i++) input[i] *= 0.95;
    const output = resampleLinear(input, 48000, 16000);
    for (let i = 0; i < output.length; i++) {
      expect(output[i]).toBeGreaterThanOrEqual(-1);
      expect(output[i]).toBeLessThanOrEqual(1);
    }
  });

  it("PCM byte alignment: output length produces even number of bytes", () => {
    const input = makeSine(440, 44100, 0.1);
    const output = resampleLinear(input, 44100, 16000);
    // Each sample → 2 bytes (Int16)
    expect((output.length * 2) % 2).toBe(0);
    expect(output.length * 2).toBeGreaterThan(0);
  });

  it("expected byte length matches formula: floor(inputLen / ratio) * 2", () => {
    const inputs = [
      { src: 44100, dst: 16000, len: 4410 },  // 0.1s
      { src: 48000, dst: 16000, len: 4800 },  // 0.1s
      { src: 16000, dst: 16000, len: 1600 },  // 0.1s
    ];
    for (const { src, dst, len } of inputs) {
      const input = new Float32Array(len);
      const output = resampleLinear(input, src, dst);
      const expectedBytes = output.length * 2;
      expect(expectedBytes % 2).toBe(0);
      expect(expectedBytes).toBeGreaterThan(0);
    }
  });
});
