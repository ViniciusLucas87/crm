"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, ExternalLink, Linkedin, Loader2, Plus, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type Campaign = { id: number; name: string; audience: string; communities: string[]; offer_summary: string };
type Status = { message: string; rules: string[] };
type Opportunity = {
  id: number; community: string; author_handle: string; post_title: string; post_excerpt: string;
  source_url: string; relevance_score: number; relevance_reason: string; status: string;
  public_reply_draft?: string | null; dm_draft?: string | null; permission_basis?: string | null;
  human_approved_at?: string | null; contacted_at?: string | null;
};

const labels: Record<string, string> = { watch: "Research", public_reply_ready: "Note ready", dm_ready: "Approved", contacted: "Contacted", follow_up: "Follow up", won: "Won", closed: "Closed" };

export default function LinkedInLeadsPage() {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [items, setItems] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [reasons, setReasons] = useState<Record<number, string>>({});
  const [form, setForm] = useState({
    community: "Canada", author_handle: "", post_title: "", post_excerpt: "", source_url: "",
    relevance_score: 75, relevance_reason: "Canadian contractor owner with a documented missed-call or after-hours response problem.",
  });

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [c, s, o] = await Promise.all([
        fetch("/api/linkedin/campaigns", { cache: "no-store" }),
        fetch("/api/linkedin/status", { cache: "no-store" }),
        fetch("/api/linkedin/opportunities", { cache: "no-store" }),
      ]);
      if (!c.ok || !s.ok || !o.ok) throw new Error();
      setCampaign((await c.json()).items?.[0] ?? null);
      setStatus(await s.json()); setItems((await o.json()).items ?? []);
    } catch { setError("The LinkedIn workspace could not be loaded. Your CRM data is safe."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  async function add() {
    setSaving(true); setError(""); setSuccess("");
    try {
      const response = await fetch("/api/linkedin/opportunities", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, campaign_id: campaign?.id, detected_signals: ["missed calls", "Canadian contractor"] }) });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "The owner could not be saved.");
      setShowAdd(false); setForm({ ...form, author_handle: "", post_title: "", post_excerpt: "", source_url: "" }); await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The owner could not be saved."); }
    finally { setSaving(false); }
  }
  async function draft(id: number) {
    setSaving(true); setError(""); setSuccess("");
    try {
      const response = await fetch(`/api/linkedin/opportunities/${id}/draft`, { method: "POST" });
      if (!response.ok) throw new Error("The connection note could not be prepared.");
      await load(); setSuccess("Connection note prepared for your review.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The connection note could not be prepared."); }
    finally { setSaving(false); }
  }
  async function approve(item: Opportunity) {
    const reason = reasons[item.id]?.trim() || item.relevance_reason.trim() || "Owner profile and personalized note reviewed by Vini.";
    setSaving(true); setError(""); setSuccess("");
    try {
      const response = await fetch(`/api/linkedin/opportunities/${item.id}/approve-dm`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ human_approved: true, permission_basis: reason }) });
      if (!response.ok) throw new Error("The connection note could not be approved.");
      await load(); setSuccess(`${item.author_handle}'s note is approved and ready to send.`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The connection note could not be approved."); }
    finally { setSaving(false); }
  }
  async function approveAll() {
    const prepared = items.filter(item => item.public_reply_draft && !item.human_approved_at);
    if (prepared.length === 0) { setSuccess("Every prepared note is already approved."); return; }
    setSaving(true); setError(""); setSuccess("");
    try {
      const responses = await Promise.all(prepared.map(item => fetch(`/api/linkedin/opportunities/${item.id}/approve-dm`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ human_approved: true, permission_basis: reasons[item.id]?.trim() || item.relevance_reason.trim() || "Owner profile and personalized note reviewed by Vini." }),
      })));
      if (responses.some(response => !response.ok)) throw new Error("At least one connection note could not be approved.");
      await load(); setSuccess(`${prepared.length} connection ${prepared.length === 1 ? "note is" : "notes are"} approved and ready to send.`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The connection notes could not be approved."); }
    finally { setSaving(false); }
  }
  async function contacted(id: number) {
    setSaving(true); setError(""); setSuccess("");
    try {
      const response = await fetch(`/api/linkedin/opportunities/${id}/mark-contacted`, { method: "POST" });
      if (!response.ok) throw new Error("The sent connection could not be recorded.");
      await load(); setSuccess("Contact recorded in the CRM.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The sent connection could not be recorded."); }
    finally { setSaving(false); }
  }

  return <div className="space-y-6">
    <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "LinkedIn Opportunities" }]} />
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">Owner outreach</p><h1 className="mt-1 text-2xl font-semibold text-white">LinkedIn Opportunities</h1><p className="mt-1 max-w-2xl text-sm text-slate-400">Research Canadian contractor owners, prepare a personal connection note, and record the result.</p></div>
      <div className="flex gap-2"><Button variant="secondary" onClick={() => void load()}><RefreshCw className="mr-1 h-4 w-4" />Refresh</Button><Button variant="primary" onClick={() => setShowAdd(v => !v)}><Plus className="mr-1 h-4 w-4" />Add owner</Button></div>
    </div>
    {error && <Card className="border-red-400/20 bg-red-400/5"><p className="text-sm text-red-300">{error}</p></Card>}
    {success && <Card className="border-emerald-400/20 bg-emerald-400/5"><div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /><p className="text-sm text-emerald-200">{success}</p></div></Card>}
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2"><div className="flex items-center gap-2"><Linkedin className="h-5 w-5 text-cyan-400" /><h2 className="font-semibold text-white">{campaign?.name || "Canadian contractor outreach"}</h2></div><p className="mt-2 text-sm text-slate-300">{campaign?.audience}</p><p className="mt-3 text-sm text-slate-400">{campaign?.offer_summary}</p><div className="mt-4 flex flex-wrap gap-2">{campaign?.communities.map(place => <Badge key={place}>{place}</Badge>)}</div></Card>
      <Card className="border-emerald-400/15 bg-emerald-400/5"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-emerald-400" /><h2 className="font-semibold text-white">Profile protection</h2></div><p className="mt-2 text-sm text-slate-300">{status?.message || "Checking workflow"}</p><p className="mt-3 text-xs text-slate-500">No scraping or automatic bulk messages. You approve each contact.</p></Card>
    </div>
    {showAdd && <Card><h2 className="font-semibold text-white">Save a researched owner</h2><p className="mt-1 text-xs text-slate-500">Use Google and public company information to confirm the owner and the business need.</p><div className="mt-4 grid gap-3 md:grid-cols-2">
      <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white" placeholder="Province or city" value={form.community} onChange={e => setForm({ ...form, community: e.target.value })} />
      <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white" placeholder="Owner name" value={form.author_handle} onChange={e => setForm({ ...form, author_handle: e.target.value })} />
      <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="Company and role" value={form.post_title} onChange={e => setForm({ ...form, post_title: e.target.value })} />
      <textarea className="min-h-24 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="Research evidence" value={form.post_excerpt} onChange={e => setForm({ ...form, post_excerpt: e.target.value })} />
      <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="LinkedIn profile URL" value={form.source_url} onChange={e => setForm({ ...form, source_url: e.target.value })} />
      <textarea className="min-h-20 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="Why Never Miss may help" value={form.relevance_reason} onChange={e => setForm({ ...form, relevance_reason: e.target.value })} />
    </div><div className="mt-4 flex justify-end"><Button variant="primary" onClick={() => void add()} disabled={saving}>Save for review</Button></div></Card>}
    <Card><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold text-white">Owner queue</h2><span className="text-xs text-slate-500">{items.length} owners</span></div><Button variant="secondary" size="sm" disabled={saving || !items.some(item => item.public_reply_draft && !item.human_approved_at)} onClick={() => void approveAll()}>{saving ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="mr-1 h-3.5 w-3.5" />}Approve all prepared notes</Button></div>
      {loading ? <div className="py-12 text-center"><Loader2 className="mx-auto h-6 w-6 animate-spin text-cyan-400" /></div> : items.length === 0 ? <div className="py-12 text-center"><Linkedin className="mx-auto h-8 w-8 text-slate-600" /><p className="mt-3 text-sm text-white">No LinkedIn owners researched yet</p></div> : <div className="mt-4 space-y-3">{items.map(item => <div key={item.id} className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex flex-wrap gap-2"><Badge>{item.community}</Badge><Badge variant={item.relevance_score >= 75 ? "success" : "warning"}>{item.relevance_score}% fit</Badge><Badge>{labels[item.status] || item.status}</Badge></div><h3 className="mt-2 font-medium text-white">{item.author_handle}</h3><p className="text-sm text-cyan-200">{item.post_title}</p><p className="mt-2 text-sm text-slate-400">{item.post_excerpt}</p><p className="mt-2 text-xs text-cyan-200">Why it matters: {item.relevance_reason}</p></div><a href={item.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-cyan-400">Open profile <ExternalLink className="h-3 w-3" /></a></div>
        {item.public_reply_draft && <div className="mt-3 rounded-lg border border-cyan-400/10 bg-cyan-400/5 p-3"><p className="text-xs font-semibold text-cyan-300">Connection note</p><p className="mt-1 text-sm text-slate-300">{item.public_reply_draft}</p></div>}
        {!item.public_reply_draft ? <div className="mt-3 flex justify-end"><Button variant="secondary" size="sm" disabled={saving} onClick={() => void draft(item.id)}><Sparkles className="mr-1 h-3.5 w-3.5" />Prepare connection note</Button></div> : !item.human_approved_at ? <div className="mt-3 rounded-lg border border-amber-400/15 bg-amber-400/5 p-3"><p className="text-xs text-slate-400">Review the profile and note. The research reason below will be saved with your approval, or you can add your own.</p><textarea className="mt-3 min-h-16 w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white" placeholder={item.relevance_reason || "Optional approval note"} value={reasons[item.id] || ""} onChange={e => setReasons(current => ({ ...current, [item.id]: e.target.value }))} /><div className="mt-3 flex justify-end"><Button variant="secondary" size="sm" disabled={saving} onClick={() => void approve(item)}>{saving && <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />}Approve note</Button></div></div> : <div className="mt-3 rounded-lg border border-emerald-400/15 bg-emerald-400/5 p-3"><div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /><p className="text-xs font-semibold text-emerald-200">Approved for personal sending</p></div>{item.dm_draft && <p className="mt-3 text-sm text-slate-300">{item.dm_draft}</p>}<div className="mt-3 flex justify-end">{item.contacted_at ? <Badge variant="success">Contact recorded</Badge> : <Button variant="primary" size="sm" disabled={saving} onClick={() => void contacted(item.id)}>I sent this</Button>}</div></div>}
      </div>)}</div>}
    </Card>
  </div>;
}
