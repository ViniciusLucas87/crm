"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Send, Mail, MessageSquare, Phone, Lightbulb, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Lead = {
  id: number; name: string; industry: string | null; city: string | null;
  status: string; opportunity_score: number | null;
  outreach_data: string | null;
};

export default function OutreachQueuePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetch("/api/leads/?status=approved&page_size=20")
      .then(r => r.json())
      .then(d => setLeads(d.items || []))
      .finally(() => setLoading(false));
  }, []);

  const generateOutreach = async (id: number) => {
    setGenerating(prev => new Set(prev).add(id));
    await fetch(`/api/leads/${id}/outreach/generate`, { method: "POST" });
    setGenerating(prev => { const s = new Set(prev); s.delete(id); return s; });
    // Refresh
    const r = await fetch("/api/leads/?status=approved&page_size=20");
    const d = await r.json();
    setLeads(d.items || []);
  };

  const hasOutreach = (l: Lead) => {
    if (!l.outreach_data) return false;
    try { const d = JSON.parse(l.outreach_data); return d && Object.keys(d).length > 0; } catch { return false; }
  };

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Outreach Queue" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Outreach Queue</h2>
          <p className="text-sm text-slate-400">AI-generated outreach for approved leads.</p>
        </div>
        <Link href="/leads/import-review" className="text-xs text-slate-400 hover:text-cyan-300">Import Review →</Link>
      </div>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
      ) : leads.length === 0 ? (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-12 text-center">
            <Send className="mx-auto h-10 w-10 text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">No Approved Leads</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Approve leads from your workspace first. Then generate AI outreach content including cold emails, LinkedIn messages, and call scripts.
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {leads.map(lead => {
            const ready = hasOutreach(lead);
            return (
              <Card key={lead.id}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`rounded-lg p-2 ${ready ? "bg-emerald-400/10" : "bg-amber-400/10"}`}>
                      <Send className={`h-5 w-5 ${ready ? "text-emerald-400" : "text-amber-400"}`} />
                    </div>
                    <div>
                      <Link href={`/leads/${lead.id}` as Route} target="_blank" rel="noopener noreferrer" className="font-medium text-white hover:text-cyan-300">{lead.name}</Link>
                      <p className="text-xs text-slate-400">{lead.industry} {lead.city ? `· ${lead.city}` : ""}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {lead.opportunity_score != null && <Badge variant={lead.opportunity_score >= 70 ? "success" : "warning"}>{lead.opportunity_score}</Badge>}
                    {ready ? (
                      <Link href={`/leads/${lead.id}` as Route} target="_blank" rel="noopener noreferrer">
                        <Button variant="secondary" size="sm">View Outreach</Button>
                      </Link>
                    ) : (
                      <Button variant="primary" size="sm" onClick={() => generateOutreach(lead.id)} disabled={generating.has(lead.id)}>
                        <Sparkles className="mr-1 h-3 w-3" />
                        {generating.has(lead.id) ? "Generating..." : "Generate"}
                      </Button>
                    )}
                  </div>
                </div>
                {ready && (
                  <div className="mt-3 flex gap-2 text-xs">
                    <span className="flex items-center gap-1 text-emerald-400"><Mail className="h-3 w-3" />Email</span>
                    <span className="flex items-center gap-1 text-blue-400"><MessageSquare className="h-3 w-3" />LinkedIn</span>
                    <span className="flex items-center gap-1 text-amber-400"><Phone className="h-3 w-3" />Call Script</span>
                    <span className="flex items-center gap-1 text-purple-400"><Lightbulb className="h-3 w-3" />Discovery Qs</span>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
