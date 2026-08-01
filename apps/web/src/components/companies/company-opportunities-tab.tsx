"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Target } from "lucide-react";

type Opp = {
  id: number; title: string; stage: string;
  estimated_value: number; probability: number;
  expected_close_date?: string;
};

const STAGE_COLORS: Record<string, "success" | "warning" | "neutral"> = {
  lead: "neutral", qualified: "warning", proposal: "warning",
  negotiation: "warning", won: "success", lost: "neutral",
};

export function CompanyOpportunitiesTab({ companyId }: { companyId: number }) {
  const [opps, setOpps] = useState<Opp[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchOpps = useCallback(async () => {
    try {
      const r = await fetch(`/api/opportunities?company_id=${companyId}`);
      const d = await r.json();
      setOpps(d.items || []);
    } finally { setLoading(false); }
  }, [companyId]);

  useEffect(() => { fetchOpps(); }, [fetchOpps]);

  if (loading) return <div className="space-y-2">{[1,2].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}</div>;

  if (opps.length === 0) {
    return (
      <Card className="border-white/5 bg-slate-800/30 py-10 text-center">
        <Target className="mx-auto h-8 w-8 text-slate-600 mb-2" />
        <p className="text-sm text-slate-400">No opportunities yet.</p>
        <p className="text-xs text-slate-500 mt-1">Pipeline opportunities will appear here when created.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {opps.map(o => (
        <Card key={o.id} className="border-white/5 bg-slate-800/20 p-3 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white">{o.title}</p>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={STAGE_COLORS[o.stage] || "neutral"}>{o.stage}</Badge>
              <span className="text-xs text-amber-400">${Number(o.estimated_value).toLocaleString()}</span>
              <span className="text-xs text-slate-500">{o.probability}%</span>
            </div>
          </div>
          {o.expected_close_date && <span className="text-xs text-slate-600 shrink-0">{new Date(o.expected_close_date).toLocaleDateString()}</span>}
        </Card>
      ))}
    </div>
  );
}
