"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Inbox, MessageSquareText, PhoneMissed, RefreshCw, Save } from "lucide-react";
import { Button } from "@/components/ui/button";

type ProductConfig = {
  enabled: boolean;
  plan: string;
  business_name: string | null;
  business_phone: string | null;
  notification_phone: string | null;
  recovery_message: string | null;
  monthly_call_limit: number;
  monthly_message_limit: number;
};

type NeverMissSummary = {
  missed_calls: number;
  automatic_messages_sent: number;
  callbacks_open: number;
  recent: Array<{ id: number; phone: string; status: string; message_status: string | null; occurred_at: string }>;
};

type CapturedLead = {
  id: number;
  source: string;
  name: string | null;
  company_name: string | null;
  email: string | null;
  phone: string | null;
  summary: string | null;
  status: string;
  priority: string;
  next_action: string | null;
  created_at: string;
};

type PilotAccount = {
  id: number; business_name: string; customer_email: string; plan: string; status: string;
  assigned_phone: string | null; existing_phone: string | null; setup_ready: boolean;
  calls: number; messages_sent: number; last_call_at: string | null; last_error: string | null;
};

const emptyConfig: ProductConfig = {
  enabled: false,
  plan: "never_miss",
  business_name: "",
  business_phone: "",
  notification_phone: "",
  recovery_message: "Thanks for calling. We are helping another customer, but we would like to assist you. Please reply with your name and a short description of what you need.",
  monthly_call_limit: 50,
  monthly_message_limit: 100,
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { cache: "no-store", ...init });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || payload.error || "The request could not be completed");
  return payload as T;
}

export function NeverMissScreen() {
  const [config, setConfig] = useState<ProductConfig>(emptyConfig);
  const [summary, setSummary] = useState<NeverMissSummary | null>(null);
  const [leads, setLeads] = useState<CapturedLead[]>([]);
  const [testers, setTesters] = useState<PilotAccount[]>([]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [leadName, setLeadName] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [leadSummary, setLeadSummary] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [nextConfig, nextSummary, inbox, pilot] = await Promise.all([
        api<ProductConfig>("/api/products/never_miss/configuration"),
        api<NeverMissSummary>("/api/products/never_miss/summary"),
        api<{ items: CapturedLead[] }>("/api/products/never_miss_plus/inbox"),
        api<{ items: PilotAccount[] }>("/api/products/never_miss/testers").catch(() => ({ items: [] })),
      ]);
      setConfig(nextConfig);
      setSummary(nextSummary);
      setLeads(inbox.items);
      setTesters(pilot.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The product workspace is unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function saveConfiguration(event: FormEvent) {
    event.preventDefault();
    setNotice("");
    setError("");
    try {
      const updated = await api<ProductConfig>("/api/products/never_miss/configuration", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...config, business_hours_json: { timezone: "America/Vancouver" } }),
      });
      setConfig(updated);
      setNotice("Never Miss configuration saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Configuration could not be saved");
    }
  }

  async function createLead(event: FormEvent) {
    event.preventDefault();
    setNotice("");
    setError("");
    try {
      await api("/api/products/never_miss_plus/intake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "manual", name: leadName, phone: leadPhone, summary: leadSummary }),
      });
      setLeadName("");
      setLeadPhone("");
      setLeadSummary("");
      setNotice("Lead added to the unified inbox");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lead could not be added");
    }
  }

  async function updateStatus(id: number, status: string) {
    setError("");
    try {
      const updated = await api<CapturedLead>(`/api/products/never_miss_plus/inbox/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setLeads((current) => current.map((lead) => lead.id === id ? updated : lead));
      setNotice(`Lead marked ${status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lead status could not be updated");
    }
  }

  if (loading) return <p className="text-slate-400">Loading Never Miss...</p>;

  const inputClass = "w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-400/60";
  const cardClass = "rounded-2xl border border-white/10 bg-white/5 p-5";

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Never Miss</p>
        <h1 className="mt-1 text-3xl font-semibold text-white">Missed Call Recovery</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-400">Reply to missed callers automatically and keep every callback in one place.</p>
      </div>

      {(notice || error) && <div className={`rounded-xl border px-4 py-3 text-sm ${error ? "border-amber-400/30 bg-amber-950/20 text-amber-200" : "border-cyan-400/30 bg-cyan-950/20 text-cyan-100"}`}>{error || notice}</div>}

      <section className="space-y-4">
        <div className="flex items-center gap-3"><PhoneMissed className="text-cyan-300" /><div><h2 className="text-xl font-semibold text-white">Pilot accounts</h2><p className="text-sm text-slate-400">See who finished setup and whether real calls and replies are reaching the service.</p></div></div>
        <div className="overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="bg-white/5 text-slate-400"><tr><th className="p-4">Customer</th><th className="p-4">Service</th><th className="p-4">Connection</th><th className="p-4">Calls</th><th className="p-4">Texts</th><th className="p-4">Last activity</th></tr></thead>
            <tbody className="divide-y divide-white/10">
              {testers.map((tester) => <tr key={tester.id} className="text-slate-200"><td className="p-4"><p className="font-semibold text-white">{tester.business_name}</p><p className="text-xs text-slate-500">{tester.customer_email}</p></td><td className="p-4"><p>{tester.plan === "never_miss_plus" ? "Never Miss Plus" : "Never Miss"}</p><p className="text-xs text-slate-500">{tester.status}</p></td><td className="p-4"><span className={`rounded-full px-3 py-1 text-xs font-semibold ${tester.setup_ready ? "bg-emerald-400/15 text-emerald-200" : "bg-amber-400/15 text-amber-200"}`}>{tester.setup_ready ? "Ready" : "Needs setup"}</span>{tester.last_error ? <p className="mt-2 max-w-xs text-xs text-amber-200">{tester.last_error}</p> : null}</td><td className="p-4">{tester.calls}</td><td className="p-4">{tester.messages_sent}</td><td className="p-4 text-slate-400">{tester.last_call_at ? new Date(tester.last_call_at).toLocaleString() : "No call yet"}</td></tr>)}
              {testers.length === 0 ? <tr><td colSpan={6} className="p-6 text-center text-slate-400">No pilot accounts yet.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3"><PhoneMissed className="text-cyan-300" /><div><h2 className="text-xl font-semibold text-white">Never Miss</h2><p className="text-sm text-slate-400">$39/month · Automatic reply and callback reminders.</p></div></div>
          <Button onClick={() => void load()}><RefreshCw className="mr-2 inline h-4 w-4" />Refresh</Button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Missed calls", summary?.missed_calls ?? 0],
            ["Automatic replies", summary?.automatic_messages_sent ?? 0],
            ["Callbacks open", summary?.callbacks_open ?? 0],
          ].map(([label, value]) => <div key={String(label)} className={cardClass}><p className="text-sm text-slate-400">{label}</p><p className="mt-2 text-3xl font-semibold text-white">{value}</p></div>)}
        </div>

        <form onSubmit={saveConfiguration} className={`${cardClass} grid gap-4 md:grid-cols-2`}>
          <label className="text-sm text-slate-300">Business name<input className={`${inputClass} mt-1`} value={config.business_name ?? ""} onChange={(e) => setConfig({ ...config, business_name: e.target.value })} /></label>
          <label className="text-sm text-slate-300">Business phone<input className={`${inputClass} mt-1`} value={config.business_phone ?? ""} onChange={(e) => setConfig({ ...config, business_phone: e.target.value })} placeholder="+16045550100" /></label>
          <label className="text-sm text-slate-300">Notification phone<input className={`${inputClass} mt-1`} value={config.notification_phone ?? ""} onChange={(e) => setConfig({ ...config, notification_phone: e.target.value })} placeholder="+16045550101" /></label>
          <label className="text-sm text-slate-300">Package<select className={`${inputClass} mt-1`} value={config.plan} onChange={(e) => setConfig({ ...config, plan: e.target.value })}><option value="never_miss">Never Miss · $39/month</option><option value="never_miss_plus">Never Miss Plus · $89/month</option></select></label>
          <label className="text-sm text-slate-300 md:col-span-2">Recovery message<textarea className={`${inputClass} mt-1 min-h-24`} value={config.recovery_message ?? ""} onChange={(e) => setConfig({ ...config, recovery_message: e.target.value })} /></label>
          <label className="flex items-center gap-3 text-sm text-slate-300"><input type="checkbox" checked={config.enabled} onChange={(e) => setConfig({ ...config, enabled: e.target.checked })} />Enable missed call recovery</label>
          <div className="text-right"><Button variant="primary" type="submit"><Save className="mr-2 inline h-4 w-4" />Save configuration</Button></div>
        </form>
      </section>

      <section className="space-y-4">
        <div className="flex items-center gap-3"><Inbox className="text-cyan-300" /><div><h2 className="text-xl font-semibold text-white">Never Miss Plus</h2><p className="text-sm text-slate-400">$89/month · Everything in Never Miss, plus one inbox for calls, texts, forms, and website inquiries.</p></div></div>
        <form onSubmit={createLead} className={`${cardClass} grid gap-3 md:grid-cols-4`}>
          <input required className={inputClass} placeholder="Contact name" value={leadName} onChange={(e) => setLeadName(e.target.value)} />
          <input className={inputClass} placeholder="Phone number" value={leadPhone} onChange={(e) => setLeadPhone(e.target.value)} />
          <input className={inputClass} placeholder="What do they need?" value={leadSummary} onChange={(e) => setLeadSummary(e.target.value)} />
          <Button variant="primary" type="submit"><MessageSquareText className="mr-2 inline h-4 w-4" />Add inquiry</Button>
        </form>

        <div className="space-y-3">
          {leads.length === 0 && <div className={cardClass}><p className="text-slate-400">No captured inquiries yet. Add one above or connect a website form using the intake API.</p></div>}
          {leads.map((lead) => (
            <article key={lead.id} className={`${cardClass} flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between`}>
              <div><div className="flex items-center gap-2"><h3 className="font-semibold text-white">{lead.name || lead.company_name || lead.phone || "Unknown contact"}</h3><span className="rounded-full bg-cyan-400/10 px-2 py-0.5 text-xs text-cyan-200">{lead.source}</span></div><p className="mt-1 text-sm text-slate-400">{lead.summary || "No request summary"}</p><p className="mt-1 text-xs text-slate-500">{lead.phone || lead.email || "No contact detail"} · {new Date(lead.created_at).toLocaleString()}</p></div>
              <div className="flex flex-wrap gap-2">{["contacted", "qualified", "booked", "won", "lost"].map((status) => <Button key={status} variant={lead.status === status ? "primary" : "ghost"} onClick={() => void updateStatus(lead.id, status)}>{status}</Button>)}</div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
