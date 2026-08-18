"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, ExternalLink, Loader2, MessageCircle, Plus, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type Campaign = {
  id: number;
  name: string;
  product_code: string;
  audience: string;
  communities: string[];
  pain_signals: string[];
  offer_summary: string;
};

type Opportunity = {
  id: number;
  community: string;
  author_handle: string;
  post_title: string;
  post_excerpt: string;
  source_url: string;
  relevance_score: number;
  relevance_reason: string;
  detected_signals: string[];
  status: string;
  public_reply_draft?: string | null;
  dm_draft?: string | null;
  permission_basis?: string | null;
  human_approved_at?: string | null;
  contacted_at?: string | null;
};

type RedditStatus = {
  connected: boolean;
  api_configured: boolean;
  message: string;
  rules: string[];
};

const STAGE_LABELS: Record<string, string> = {
  watch: "Watch",
  public_reply_ready: "Reply ready",
  engaged: "Engaged",
  permission_received: "Permission received",
  dm_ready: "DM ready",
  contacted: "Contacted",
  follow_up: "Follow up",
  won: "Won",
  closed: "Closed",
};

export default function RedditLeadsPage() {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [status, setStatus] = useState<RedditStatus | null>(null);
  const [items, setItems] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [permissionNotes, setPermissionNotes] = useState<Record<number, string>>({});
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    community: "Contractor",
    author_handle: "",
    post_title: "",
    post_excerpt: "",
    source_url: "",
    relevance_score: 70,
    relevance_reason: "The author appears to run a service business and describes a missed call or callback problem.",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [campaignsResponse, statusResponse, opportunitiesResponse] = await Promise.all([
        fetch("/api/reddit/campaigns", { cache: "no-store" }),
        fetch("/api/reddit/status", { cache: "no-store" }),
        fetch("/api/reddit/opportunities", { cache: "no-store" }),
      ]);
      if (!campaignsResponse.ok || !statusResponse.ok || !opportunitiesResponse.ok) throw new Error();
      const campaignsData = await campaignsResponse.json();
      const statusData = await statusResponse.json();
      const opportunitiesData = await opportunitiesResponse.json();
      setCampaign(campaignsData.items?.[0] ?? null);
      setStatus(statusData);
      setItems(opportunitiesData.items ?? []);
    } catch {
      setError("The Reddit workspace could not be loaded. Your existing CRM data is safe.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function addConversation() {
    setSaving(true);
    setError("");
    try {
      const response = await fetch("/api/reddit/opportunities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, campaign_id: campaign?.id, detected_signals: ["missed calls"] }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "The conversation could not be saved.");
      }
      setShowAdd(false);
      setForm({ ...form, author_handle: "", post_title: "", post_excerpt: "", source_url: "" });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The conversation could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function draft(id: number) {
    setSaving(true);
    const response = await fetch(`/api/reddit/opportunities/${id}/draft`, { method: "POST" });
    if (!response.ok) setError("A response could not be prepared right now.");
    await load();
    setSaving(false);
  }

  async function approvePrivateMessage(id: number) {
    const permissionBasis = permissionNotes[id]?.trim();
    if (!permissionBasis || permissionBasis.length < 5) {
      setError("Explain how this person invited or agreed to a private message.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`/api/reddit/opportunities/${id}/approve-dm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ human_approved: true, permission_basis: permissionBasis }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "The private message could not be approved.");
      }
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The private message could not be approved.");
    } finally {
      setSaving(false);
    }
  }

  async function markContacted(id: number) {
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`/api/reddit/opportunities/${id}/mark-contacted`, { method: "POST" });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "The conversation could not be marked as contacted.");
      }
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The conversation could not be marked as contacted.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Reddit Opportunities" }]} />

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">Community selling</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Reddit Opportunities</h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-400">Find real conversations where Never Miss can help. Be useful first, earn permission, then continue privately.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => void load()} disabled={loading}><RefreshCw className="mr-1 h-4 w-4" />Refresh</Button>
          <Button variant="primary" onClick={() => setShowAdd(value => !value)}><Plus className="mr-1 h-4 w-4" />Add conversation</Button>
        </div>
      </div>

      {error && <Card className="border-red-400/20 bg-red-400/5"><p className="text-sm text-red-300">{error}</p></Card>}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-cyan-400" /><h2 className="font-semibold text-white">{campaign?.name || "Never Miss contractor pilot"}</h2></div>
          <p className="mt-2 text-sm text-slate-300">{campaign?.audience || "Canadian contractors and service business owners"}</p>
          <p className="mt-3 text-sm text-slate-400">{campaign?.offer_summary}</p>
          <div className="mt-4 flex flex-wrap gap-2">{campaign?.communities.map(name => <Badge key={name}>r/{name}</Badge>)}</div>
        </Card>
        <Card className="border-emerald-400/15 bg-emerald-400/5">
          <div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-emerald-400" /><h2 className="font-semibold text-white">Account protection</h2></div>
          <p className="mt-2 text-sm text-slate-300">{status?.message || "Checking Reddit connection"}</p>
          <p className="mt-3 text-xs text-slate-500">No automatic unsolicited DMs. You approve every message.</p>
        </Card>
      </div>

      {showAdd && (
        <Card>
          <h2 className="font-semibold text-white">Save a promising conversation</h2>
          <p className="mt-1 text-xs text-slate-500">This manual intake works now. Live monitoring will use the same review queue after Reddit is connected.</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white" placeholder="Community" value={form.community} onChange={event => setForm({ ...form, community: event.target.value })} />
            <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white" placeholder="Reddit username" value={form.author_handle} onChange={event => setForm({ ...form, author_handle: event.target.value })} />
            <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="Post title" value={form.post_title} onChange={event => setForm({ ...form, post_title: event.target.value })} />
            <textarea className="min-h-24 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="Relevant part of the conversation" value={form.post_excerpt} onChange={event => setForm({ ...form, post_excerpt: event.target.value })} />
            <input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="https://www.reddit.com/..." value={form.source_url} onChange={event => setForm({ ...form, source_url: event.target.value })} />
            <textarea className="min-h-20 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white md:col-span-2" placeholder="Why this person may need Never Miss" value={form.relevance_reason} onChange={event => setForm({ ...form, relevance_reason: event.target.value })} />
          </div>
          <div className="mt-4 flex justify-end"><Button variant="primary" onClick={() => void addConversation()} disabled={saving}>{saving && <Loader2 className="mr-1 h-4 w-4 animate-spin" />}Save for review</Button></div>
        </Card>
      )}

      <Card>
        <div className="flex items-center justify-between"><h2 className="font-semibold text-white">Opportunity queue</h2><span className="text-xs text-slate-500">{items.length} conversations</span></div>
        {loading ? (
          <div className="py-12 text-center"><Loader2 className="mx-auto h-6 w-6 animate-spin text-cyan-400" /><p className="mt-2 text-sm text-slate-400">Loading conversations</p></div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center"><MessageCircle className="mx-auto h-8 w-8 text-slate-600" /><p className="mt-3 text-sm font-medium text-white">No Reddit opportunities yet</p><p className="mt-1 text-xs text-slate-500">Add one useful conversation to test the review and message workflow.</p></div>
        ) : (
          <div className="mt-4 space-y-3">
            {items.map(item => (
              <div key={item.id} className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2"><Badge>r/{item.community}</Badge><span className="text-xs text-slate-500">u/{item.author_handle}</span><Badge variant={item.relevance_score >= 75 ? "success" : "warning"}>{item.relevance_score}% fit</Badge><Badge>{STAGE_LABELS[item.status] || item.status}</Badge></div>
                    <h3 className="mt-2 font-medium text-white">{item.post_title}</h3>
                    <p className="mt-1 line-clamp-2 text-sm text-slate-400">{item.post_excerpt}</p>
                    <p className="mt-2 text-xs text-cyan-200">Why it matters: {item.relevance_reason}</p>
                  </div>
                  <a href={item.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300">Open conversation <ExternalLink className="h-3 w-3" /></a>
                </div>
                {item.public_reply_draft && <div className="mt-3 rounded-lg border border-cyan-400/10 bg-cyan-400/5 p-3"><p className="text-xs font-semibold text-cyan-300">Suggested public reply</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-300">{item.public_reply_draft}</p></div>}
                {!item.public_reply_draft ? (
                  <div className="mt-3 flex justify-end"><Button variant="secondary" size="sm" onClick={() => void draft(item.id)} disabled={saving}><Sparkles className="mr-1 h-3.5 w-3.5" />Prepare helpful reply</Button></div>
                ) : !item.human_approved_at ? (
                  <div className="mt-3 rounded-lg border border-amber-400/15 bg-amber-400/5 p-3">
                    <p className="text-xs font-semibold text-amber-200">Before a private message</p>
                    <p className="mt-1 text-xs text-slate-400">Reply publicly first. Continue here only if the person asks for details or clearly agrees to a private message.</p>
                    <textarea
                      className="mt-3 min-h-20 w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
                      placeholder="What did the person say that gives us permission?"
                      value={permissionNotes[item.id] ?? item.permission_basis ?? ""}
                      onChange={event => setPermissionNotes(current => ({ ...current, [item.id]: event.target.value }))}
                    />
                    <div className="mt-3 flex justify-end"><Button variant="secondary" size="sm" onClick={() => void approvePrivateMessage(item.id)} disabled={saving}>Approve private message</Button></div>
                  </div>
                ) : (
                  <div className="mt-3 rounded-lg border border-emerald-400/15 bg-emerald-400/5 p-3">
                    <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /><p className="text-xs font-semibold text-emerald-200">Permission recorded</p></div>
                    <p className="mt-1 text-xs text-slate-400">{item.permission_basis}</p>
                    {item.dm_draft && <div className="mt-3 rounded-lg border border-white/10 bg-slate-950/50 p-3"><p className="text-xs font-semibold text-cyan-300">Approved private message</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-300">{item.dm_draft}</p></div>}
                    <div className="mt-3 flex justify-end">
                      {item.contacted_at ? <Badge variant="success">Contact recorded</Badge> : <Button variant="primary" size="sm" onClick={() => void markContacted(item.id)} disabled={saving}>I sent this message</Button>}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
