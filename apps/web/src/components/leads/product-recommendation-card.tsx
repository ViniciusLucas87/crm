"use client";

import { Card } from "@/components/ui/card";

type ProductRecData = {
  recommended_product?: string;
  reason?: string;
  estimated_price_low?: number;
  estimated_price_high?: number;
  development_time?: string;
  confidence?: number;
  email_pitch?: string;
  phone_pitch?: string;
};

export function ProductRecommendationCard({ data }: { data: string | null | undefined }) {
  const rec: ProductRecData | null = (() => {
    if (!data) return null;
    try { return JSON.parse(data); } catch { return null; }
  })();

  if (!rec || !rec.recommended_product) return null;

  const price = rec.estimated_price_low && rec.estimated_price_high
    ? `$${rec.estimated_price_low.toLocaleString()} – $${rec.estimated_price_high.toLocaleString()}`
    : "—";

  return (
    <Card className="border-purple-400/10 bg-gradient-to-r from-purple-400/5 to-pink-400/5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">🎯</span>
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-purple-300">
          Product Recommendation
        </p>
        {rec.confidence && (
          <span className="ml-auto rounded-lg bg-purple-400/10 px-2 py-0.5 text-xs text-purple-400">
            {rec.confidence}% confidence
          </span>
        )}
      </div>

      {/* Recommended Product */}
      <div className="mb-3 rounded-lg border border-white/5 bg-white/[0.02] p-3">
        <p className="text-sm font-semibold text-white">{rec.recommended_product}</p>
        <div className="mt-1 flex flex-wrap gap-2 text-xs">
          <span className="text-amber-400">{price}</span>
          <span className="text-slate-500">·</span>
          <span className="text-slate-400">{rec.development_time || "—"}</span>
        </div>
        {rec.reason && (
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">{rec.reason}</p>
        )}
      </div>

      {/* Pitches */}
      <div className="grid gap-3 sm:grid-cols-2">
        {rec.email_pitch && (
          <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-xs">✉️</span>
              <span className="text-xs font-medium text-slate-400">Email Pitch</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{rec.email_pitch}</p>
          </div>
        )}
        {rec.phone_pitch && (
          <div className="rounded-lg border border-white/5 bg-slate-800/30 p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-xs">📞</span>
              <span className="text-xs font-medium text-slate-400">Phone Pitch</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">{rec.phone_pitch}</p>
          </div>
        )}
      </div>
    </Card>
  );
}
