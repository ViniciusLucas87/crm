"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Signal, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Lead = {
  id: number; name: string; industry: string | null; city: string | null;
  opportunity_score: number | null; status: string;
  buying_signals: string | null; estimated_deal_low: number | null;
};

export default function BuyingSignalsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/leads/?page_size=50&sort=score_desc")
      .then(r => r.json())
      .then(d => setLeads(d.items || []))
      .finally(() => setLoading(false));
  }, []);

  const leadsWithSignals = leads.filter(l => l.buying_signals);

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Buying Signals" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Buying Signals</h2>
          <p className="text-sm text-slate-400">Companies sorted by strongest buying intent indicators.</p>
        </div>
        <Link href="/leads/outreach-queue" className="text-xs text-slate-400 hover:text-cyan-300">Outreach →</Link>
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      ) : leadsWithSignals.length === 0 ? (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-12 text-center">
            <Signal className="mx-auto h-10 w-10 text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">No Buying Signals Yet</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Run AI research on your leads to detect buying signals like hiring, expansion, funding, and technology modernization.
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {/* Signal summary */}
          <Card>
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Signal Distribution</h4>
            <div className="flex flex-wrap gap-3">
              {["Hiring", "Expansion", "Funding", "Modernization", "Growth", "Fleet Growth", "Digital Transformation"].map(signal => (
                <div key={signal} className="flex items-center gap-1 rounded-full border border-amber-400/20 bg-amber-400/5 px-3 py-1 text-xs text-amber-300">
                  <Signal className="h-3 w-3" />{signal}
                </div>
              ))}
            </div>
          </Card>

          {leadsWithSignals.map(lead => (
            <Link key={lead.id} href={`/leads/${lead.id}` as Route} target="_blank" rel="noopener noreferrer">
              <Card className="flex items-center justify-between transition hover:bg-white/[0.02]">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-amber-400/10 p-2"><Signal className="h-5 w-5 text-amber-400" /></div>
                  <div>
                    <p className="font-medium text-white">{lead.name}</p>
                    <p className="text-xs text-slate-400">{lead.industry} {lead.city ? `· ${lead.city}` : ""}</p>
                    <p className="mt-1 text-xs text-amber-300/80 line-clamp-1">{lead.buying_signals}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {lead.estimated_deal_low != null && <span className="text-xs text-amber-400">${lead.estimated_deal_low.toLocaleString()}</span>}
                  {lead.opportunity_score != null && <Badge variant={lead.opportunity_score >= 70 ? "success" : "warning"}>{lead.opportunity_score}</Badge>}
                  <ArrowRight className="h-4 w-4 text-slate-600" />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
