"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type GoogleMapsData = {
  provider?: string;
  stage?: string;
  status?: string;
  data?: {
    place_id?: string;
    maps_url?: string;
    primary_category?: string;
    secondary_categories?: string[];
    rating?: number;
    review_count?: number;
    business_status?: string;
    formatted_address?: string;
    formatted_phone_number?: string;
    website?: string;
    opening_hours?: Record<string, string>;
    latitude?: number;
    longitude?: number;
    service_area?: string;
    business_description?: string;
    photos_count?: number;
  };
  provenance?: Record<string, string>;
  processing_time_ms?: number;
};

export function GoogleMapsCard({ data }: { data: string | null | undefined }) {
  const parsed: GoogleMapsData | null = (() => {
    if (!data) return null;
    try { return JSON.parse(data); } catch { return null; }
  })();

  if (!parsed || parsed.status === "failed") return null;
  const d = parsed.data || {};
  const hours = d.opening_hours;

  return (
    <Card className="border-blue-400/10 bg-gradient-to-r from-blue-400/5 to-cyan-400/5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">📍</span>
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-blue-300">
          Google Maps Intelligence
        </p>
        <span className="ml-auto rounded-lg bg-blue-400/10 px-2 py-0.5 text-xs text-blue-400">
          {parsed.provider || "google_maps"}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          {d.primary_category && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 w-20 shrink-0">Category</span>
              <span className="text-white font-medium">{d.primary_category}</span>
            </div>
          )}
          {d.rating != null && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 w-20 shrink-0">Rating</span>
              <span className="text-amber-400 font-medium">
                ★ {d.rating} ({d.review_count ?? 0} reviews)
              </span>
            </div>
          )}
          {d.business_status && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 w-20 shrink-0">Status</span>
              <Badge variant="success">{d.business_status}</Badge>
            </div>
          )}
          {d.formatted_phone_number && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 w-20 shrink-0">Phone</span>
              <span className="text-slate-300">{d.formatted_phone_number}</span>
            </div>
          )}
          {d.website && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 w-20 shrink-0">Website</span>
              <a href={d.website} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline truncate">{d.website}</a>
            </div>
          )}
        </div>

        <div className="space-y-1.5">
          {d.formatted_address && (
            <div className="text-xs">
              <p className="text-slate-500 mb-0.5">Address</p>
              <p className="text-slate-300">{d.formatted_address}</p>
            </div>
          )}
          {hours && Object.keys(hours).length > 0 && (
            <div className="text-xs">
              <p className="text-slate-500 mb-0.5">Hours</p>
              {Object.entries(hours).slice(0, 4).map(([day, time]) => (
                <p key={day} className="text-slate-400 capitalize">{day}: {time}</p>
              ))}
            </div>
          )}
          {d.service_area && (
            <div className="text-xs">
              <span className="text-slate-500">Service: </span>
              <span className="text-slate-400">{d.service_area}</span>
            </div>
          )}
        </div>
      </div>

      {d.maps_url && (
        <div className="mt-2 pt-2 border-t border-white/5">
          <a href={d.maps_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline">
            📍 View on Google Maps →
          </a>
        </div>
      )}

      <div className="mt-2 pt-2 border-t border-white/5 text-xs text-slate-600">
        Source: Google Maps (LLM-researched)
        {parsed.processing_time_ms ? ` · ${(parsed.processing_time_ms / 1000).toFixed(1)}s` : ""}
      </div>
    </Card>
  );
}
