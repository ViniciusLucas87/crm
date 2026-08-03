"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Download, Shield, AlertTriangle, ArrowRight, TrendingUp, Users, Signal } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Lead = {
  id: number; name: string; industry: string | null; city: string | null;
  status: string; opportunity_score: number | null; confidence_score: number | null;
  buying_signals: string | null; estimated_deal_low: number | null;
  decision_makers_data: string | null; executive_summary: string | null;
};

export default function ImportReviewPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [importing, setImporting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const fetchApproved = useCallback(() => {
    setLoading(true);
    fetch("/api/leads/?status=approved&page_size=50")
      .then(r => r.json())
      .then(d => setLeads(d.items || []))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchApproved(); }, [fetchApproved]);

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) { next.delete(id); } else { next.add(id); }
    setSelected(next);
  };

  const importSelected = async () => {
    setImporting(true);
    const ids = selected.size > 0 ? Array.from(selected) : leads.map(l => l.id);
    let count = 0;
    for (const id of ids) {
      const r = await fetch(`/api/leads/${id}/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ create_company: true, create_opportunity: false }),
      });
      if (r.ok) count++;
    }
    setConfirmOpen(false);
    setSelected(new Set());
    setImporting(false);
    fetchApproved();
    alert(`Imported ${count} of ${ids.length} companies to CRM.`);
  };

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Import Review" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Import Review</h2>
          <p className="text-sm text-slate-400">Review and import approved leads into the CRM.</p>
        </div>
        <Link href="/leads/analytics" className="text-xs text-slate-400 hover:text-cyan-300">Analytics →</Link>
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}</div>
      ) : leads.length === 0 ? (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-12 text-center">
            <Download className="mx-auto h-10 w-10 text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">No Leads to Import</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Approve leads from your workspace first. Only approved leads appear here for CRM import.
            </p>
          </div>
        </Card>
      ) : (
        <>
          {/* Summary Banner */}
          <Card className="border-emerald-400/10 bg-emerald-400/5">
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-emerald-400" />
              <div>
                <p className="text-sm text-white">{leads.length} qualified companies ready for import</p>
                <p className="text-xs text-slate-500">Only selected companies will be imported. Duplicates are automatically detected.</p>
              </div>
              <Button variant="primary" className="ml-auto" onClick={() => setConfirmOpen(true)} disabled={importing}>
                <Download className="mr-1 h-3.5 w-3.5" />Import {selected.size > 0 ? `(${selected.size})` : "All"}
              </Button>
            </div>
          </Card>

          {/* Confirmation Modal */}
          {confirmOpen && (
            <Card className="border-amber-400/20 bg-amber-400/5">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-white">Confirm Import</p>
                  <p className="mt-1 text-sm text-slate-400">
                    {selected.size > 0
                      ? `You're about to import ${selected.size} selected companies into your CRM.`
                      : `You're about to import all ${leads.length} companies into your CRM.`
                    }
                  </p>
                  <p className="mt-1 text-xs text-slate-500">Existing CRM companies will never be duplicated. This creates new Company records.</p>
                  <div className="mt-3 flex gap-2">
                    <Button variant="primary" onClick={importSelected} disabled={importing}>
                      {importing ? "Importing..." : "Confirm Import"}
                    </Button>
                    <Button variant="secondary" onClick={() => setConfirmOpen(false)}>Cancel</Button>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Lead Cards */}
          <div className="space-y-3">
            {leads.map(lead => (
              <Card key={lead.id}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <input type="checkbox" checked={selected.has(lead.id)} onChange={() => toggleSelect(lead.id)} className="mt-1 rounded" />
                    <div>
                      <div className="flex items-center gap-2">
                        <Link href={`/leads/${lead.id}` as Route} target="_blank" rel="noopener noreferrer" className="font-medium text-white hover:text-cyan-300">{lead.name}</Link>
                        {lead.opportunity_score != null && <Badge variant={lead.opportunity_score >= 70 ? "success" : "warning"}>{lead.opportunity_score}</Badge>}
                      </div>
                      <p className="text-xs text-slate-400">{lead.industry} {lead.city ? `· ${lead.city}` : ""}</p>
                      {lead.executive_summary && (
                        <p className="mt-1 text-xs text-slate-500 line-clamp-2">{lead.executive_summary}</p>
                      )}
                      <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        {lead.estimated_deal_low != null && (
                          <span className="flex items-center gap-1 text-amber-400"><TrendingUp className="h-3 w-3" />${lead.estimated_deal_low.toLocaleString()}</span>
                        )}
                        {lead.buying_signals && (
                          <span className="flex items-center gap-1 text-purple-400"><Signal className="h-3 w-3" />Signals detected</span>
                        )}
                        {lead.decision_makers_data && (
                          <span className="flex items-center gap-1 text-cyan-400"><Users className="h-3 w-3" />DMs found</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <Link href={`/leads/${lead.id}` as Route} target="_blank" rel="noopener noreferrer" aria-label={`Open ${lead.name} in a new tab`}><ArrowRight className="h-4 w-4 text-slate-600 hover:text-cyan-400" /></Link>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
