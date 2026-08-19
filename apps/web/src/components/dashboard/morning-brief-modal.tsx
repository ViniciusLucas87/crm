"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowRight, CheckCircle2, MessageCircle, X } from "lucide-react";

type BriefItem = { title: string; description: string; reason?: string | null };
type OutreachSnapshot = {
  channel: string;
  total: number;
  contacted: number;
  ready: number;
  replies: number;
  needs_review: number;
};
type MorningBrief = {
  date: string;
  summary: string;
  actions: BriefItem[];
  outreach: OutreachSnapshot[];
  data_warnings: BriefItem[];
};

const storagePrefix = "pns-morning-brief-dismissed:";

export function MorningBriefModal() {
  const [brief, setBrief] = useState<MorningBrief | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    const isMorning = new Date().getHours() < 12;
    if (!isMorning || window.localStorage.getItem(`${storagePrefix}${today}`)) return;

    let cancelled = false;
    fetch("/api/ai/brief")
      .then((response) => response.ok ? response.json() : Promise.reject(response.status))
      .then((data: MorningBrief) => {
        if (!cancelled) {
          setBrief(data);
          setOpen(true);
        }
      })
      .catch(() => undefined);

    return () => { cancelled = true; };
  }, []);

  const close = () => {
    const today = new Date().toISOString().slice(0, 10);
    window.localStorage.setItem(`${storagePrefix}${today}`, "true");
    setOpen(false);
  };

  if (!open || !brief) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="morning-brief-title">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl border border-cyan-300/20 bg-slate-950 shadow-2xl shadow-cyan-950/40">
        <div className="flex items-start justify-between border-b border-white/10 p-6 md:p-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Morning sales briefing</p>
            <h2 id="morning-brief-title" className="mt-2 text-2xl font-semibold text-white">Here is what deserves your attention today.</h2>
            <p className="mt-2 text-sm text-slate-400">{brief.summary}</p>
          </div>
          <button type="button" onClick={close} aria-label="Close morning briefing" className="rounded-xl border border-white/10 p-2 text-slate-400 transition hover:bg-white/5 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6 p-6 md:p-8">
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Outreach tracked in CRM</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {brief.outreach.map((channel) => (
                <div key={channel.channel} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-center gap-2">
                    <MessageCircle className="h-4 w-4 text-cyan-300" />
                    <p className="font-medium capitalize text-white">{channel.channel}</p>
                  </div>
                  <p className="mt-3 text-2xl font-semibold text-white">{channel.contacted} contacted</p>
                  <p className="mt-1 text-sm text-slate-400">{channel.ready} ready to send · {channel.replies} replies recorded</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">Upwork still needs a quick inbox check because it is not connected to the CRM yet.</p>
          </section>

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Recommended order</h3>
            <div className="mt-3 space-y-2">
              {brief.actions.slice(0, 4).map((action, index) => (
                <div key={`${action.title}-${index}`} className="flex gap-3 rounded-2xl border border-cyan-300/10 bg-cyan-300/5 p-4">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-cyan-300" />
                  <div>
                    <p className="font-medium text-white">{action.title}</p>
                    <p className="mt-1 text-sm text-slate-400">{action.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {brief.data_warnings.length > 0 && (
            <section className="rounded-2xl border border-amber-300/20 bg-amber-300/5 p-4">
              <div className="flex gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
                <div>
                  <p className="font-medium text-amber-100">Data check</p>
                  {brief.data_warnings.map((warning) => <p key={warning.title} className="mt-1 text-sm text-amber-100/70">{warning.title}. {warning.description}</p>)}
                </div>
              </div>
            </section>
          )}

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button type="button" onClick={close} className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-slate-300 transition hover:bg-white/5">Close for today</button>
            <Link href="/ai/daily-brief" onClick={close} className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">
              Open full briefing <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
