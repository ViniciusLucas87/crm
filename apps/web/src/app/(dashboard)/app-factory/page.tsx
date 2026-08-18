"use client";

import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Factory, FlaskConical, Loader2, ShieldCheck, WalletCards } from "lucide-react";
import { Shell } from "@/components/dashboard/shell";
import { ApiError, fetchAppFactoryPortfolio, type AppFactoryCandidate, type AppFactoryPortfolio } from "@/lib/api";

function Metric({ label, value, note }: { label: string; value: string | number; note: string }) {
  return <div className="rounded-xl border border-white/10 bg-white/5 p-4"><p className="text-xs uppercase tracking-[0.14em] text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-white">{value}</p><p className="mt-1 text-xs text-slate-400">{note}</p></div>;
}

function CandidateCard({ candidate }: { candidate: AppFactoryCandidate }) {
  const [open, setOpen] = useState(candidate.slug === "never-forget");
  const status = candidate.eligible_for_validation ? "Ready for validation" : candidate.total_score >= 75 ? "More evidence needed" : "Research only";
  return <article className="rounded-xl border border-white/10 bg-slate-950/50 p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-semibold text-white">{candidate.name}</h2><span className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-slate-300">{candidate.proposed_format}</span></div><p className="mt-1 text-sm text-slate-400">{candidate.audience}</p></div>
      <div className="text-right"><p className="text-2xl font-semibold text-cyan-300">{candidate.total_score}</p><p className="text-[11px] uppercase tracking-wider text-slate-500">commercial score</p></div>
    </div>
    <p className="mt-4 text-sm leading-6 text-slate-200">{candidate.problem}</p>
    <div className="mt-4 flex flex-wrap gap-2 text-xs"><span className={`rounded-full px-2.5 py-1 ${candidate.eligible_for_validation ? "bg-emerald-500/15 text-emerald-300" : "bg-amber-500/10 text-amber-300"}`}>{status}</span><span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">{candidate.evidence_count} independent sources</span><span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">Risk: {candidate.risk_level}</span><span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">Proposed: {candidate.proposed_price}</span></div>
    <button className="mt-4 text-sm font-medium text-cyan-300 hover:text-cyan-200" onClick={() => setOpen(value => !value)}>{open ? "Hide research" : "Show research"}</button>
    {open && <div className="mt-4 grid gap-4 border-t border-white/10 pt-4 lg:grid-cols-2"><div><p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Current workaround</p><p className="mt-1 text-sm text-slate-300">{candidate.current_workaround}</p><p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500">Distribution thesis</p><p className="mt-1 text-sm text-slate-300">{candidate.distribution_thesis}</p><p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500">Decision</p><p className="mt-1 text-sm text-slate-300">{candidate.decision_reason}</p></div><div><p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Evidence</p>{candidate.evidence.length === 0 ? <p className="mt-2 text-sm text-amber-300">The evidence standard has not been met.</p> : <ul className="mt-2 space-y-3">{candidate.evidence.map(item => <li key={item.source_url} className="rounded-lg bg-white/5 p-3"><a href={item.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-medium text-cyan-300 hover:underline">{item.source_title}<ExternalLink className="h-3 w-3" /></a><p className="mt-1 text-xs leading-5 text-slate-400">{item.signal}</p></li>)}</ul>}</div></div>}
  </article>;
}

export default function AppFactoryPage() {
  const [portfolio, setPortfolio] = useState<AppFactoryPortfolio | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => { setError(null); fetchAppFactoryPortfolio().then(setPortfolio).catch(error => setError(error instanceof ApiError ? error.message : "The App Factory could not be loaded")); }, []);
  useEffect(load, [load]);
  return <Shell><div className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">PNS product portfolio</p><h1 className="mt-1 text-2xl font-semibold text-white">App Factory</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Research real problems, reject weak ideas, validate demand and build only products that pass the commercial, safety and cost gates.</p></div><div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200"><ShieldCheck className="mr-2 inline h-4 w-4" />Production release always requires human approval</div></div>
    {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">{error}<button onClick={load} className="ml-3 underline">Try again</button></div>}
    {!portfolio && !error && <div className="py-16 text-center"><Loader2 className="mx-auto h-7 w-7 animate-spin text-cyan-300" /><p className="mt-3 text-sm text-slate-400">Loading the product portfolio</p></div>}
    {portfolio && <><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5"><Metric label="Problems researched" value={portfolio.summary.problems_researched} note="Consumer and business" /><Metric label="Ready to validate" value={portfolio.summary.qualified_for_validation} note="Score and evidence gate" /><Metric label="Ready to build" value={portfolio.summary.qualified_for_build} note="Demand gate not passed" /><Metric label="Active experiments" value={portfolio.summary.active_experiments} note="Measured tests only" /><Metric label="Experiment budget" value={`$${(portfolio.summary.monthly_experiment_cost_limit_cents / 100).toFixed(2)}`} note="Automatic pause limit" /></div>
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]"><section><div className="mb-3 flex items-center gap-2"><Factory className="h-5 w-5 text-cyan-300" /><h2 className="text-lg font-semibold text-white">Ranked candidates</h2></div><div className="space-y-3">{portfolio.candidates.map(candidate => <CandidateCard key={candidate.id} candidate={candidate} />)}</div></section><aside className="space-y-4"><div className="rounded-xl border border-white/10 bg-white/5 p-5"><div className="flex items-center gap-2"><FlaskConical className="h-5 w-5 text-cyan-300" /><h2 className="font-semibold text-white">Human actions</h2></div><ol className="mt-3 space-y-3 text-sm text-slate-300">{portfolio.summary.human_actions.map((action, index) => <li key={action} className="flex gap-3"><span className="text-cyan-300">{index + 1}</span><span>{action}</span></li>)}</ol></div><div className="rounded-xl border border-white/10 bg-white/5 p-5"><div className="flex items-center gap-2"><WalletCards className="h-5 w-5 text-cyan-300" /><h2 className="font-semibold text-white">Factory rules</h2></div><ul className="mt-3 space-y-2 text-sm text-slate-300"><li>Minimum commercial score: 75</li><li>Minimum independent sources: 3</li><li>No automatic production release</li><li>No automatic private outreach</li><li>No shared production credentials</li></ul></div></aside></div></>}
  </div></Shell>;
}
