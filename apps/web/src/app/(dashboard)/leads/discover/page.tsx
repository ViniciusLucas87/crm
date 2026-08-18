"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Sparkles, Bookmark, Loader2, TrendingUp, CheckCircle, Target } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type DiscoveredCompany = {
  name: string; industry: string; city: string; province: string;
  employees: number | null; description: string;
  executive_summary: string; opportunity_score: number;
  confidence_score: number; buying_signals: string;
  recommended_services: string; estimated_deal_low: number | null;
  estimated_deal_high: number | null; technology_maturity: string;
  revenue_estimate: string;
};

type DiscoveryResponse = {
  stage: string; progress_pct: number; message: string;
  total_time_ms: number; companies: DiscoveredCompany[];
  leads_created: number; duplicates_skipped: number;
};

const INDUSTRIES = ["Construction", "Property Management", "Engineering", "Manufacturing", "Architecture", "HVAC", "Electrical", "Marine", "Logistics", "Agriculture"];
const CITIES = ["Vancouver", "Surrey", "Burnaby", "Richmond", "Langley", "Abbotsford", "Kelowna", "Victoria", "Nanaimo", "Kamloops"];
const QUICK_SEARCHES = [
  { title: "Construction Vancouver", industry: "Construction", city: "Vancouver" },
  { title: "Property Managers BC", industry: "Property Management", city: "" },
  { title: "Engineering Firms", industry: "Engineering", city: "" },
  { title: "HVAC Contractors", industry: "HVAC", city: "" },
  { title: "Manufacturing BC", industry: "Manufacturing", city: "" },
  { title: "Marine Services", industry: "Marine", city: "Vancouver" },
];

export default function DiscoverPage() {
  const [industry, setIndustry] = useState("");
  const [city, setCity] = useState("");
  const [keyword, setKeyword] = useState("");
  const [count, setCount] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiscoveryResponse | null>(null);
  const [error, setError] = useState("");

  const runDiscovery = async (ind: string, cty: string, kw: string = "") => {
    setLoading(true); setError(""); setResult(null);
    setIndustry(ind); setCity(cty); setKeyword(kw);
    try {
      const r = await fetch("/api/leads/discover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ industry: ind, city: cty, keyword: kw, count }),
      });
      if (!r.ok) {
        setError("We couldn't complete this search right now. Your existing leads are safe. Please try again in a moment.");
        return;
      }
      const d: DiscoveryResponse = await r.json();
      if (d.stage === "error") {
        setError(d.message || "The research service could not run this search. No contacts were created.");
        return;
      }
      setResult(d);
    } catch {
      setError("We couldn't reach the research service. Your existing leads are safe. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Discover" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">AI Prospect Discovery</h2>
          <p className="text-sm text-slate-400">AI finds candidate companies. Enrichment runs only after you approve a lead.</p>
        </div>
        <Link href="/leads/saved-searches"><Button variant="secondary" size="sm"><Bookmark className="mr-1 h-3.5 w-3.5" />Saved</Button></Link>
      </div>

      {/* Search Form */}
      <Card>
        <div className="grid gap-3 sm:grid-cols-5">
          <select value={industry} onChange={e => setIndustry(e.target.value)}
            className="rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none">
            <option value="">All Industries</option>
            {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
          </select>
          <select value={city} onChange={e => setCity(e.target.value)}
            className="rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none">
            <option value="">All Cities</option>
            {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="text" placeholder="Keyword (optional)" value={keyword} onChange={e => setKeyword(e.target.value)}
            className="rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none" />
          <select value={count} onChange={e => setCount(Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white focus:border-cyan-400/50 focus:outline-none">
            {[3, 5, 10].map(n => <option key={n} value={n}>{n} companies</option>)}
          </select>
          <Button variant="primary" onClick={() => runDiscovery(industry, city, keyword)} disabled={loading}>
            {loading ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Sparkles className="mr-1 h-3.5 w-3.5" />}
            {loading ? "Researching..." : "Discover"}
          </Button>
        </div>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-8 text-center">
            <Loader2 className="mx-auto h-10 w-10 animate-spin text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">Finding good-fit companies</h3>
            <p className="mt-1 text-sm text-slate-400">
              Searching for {industry || "companies"}{city ? ` in ${city}` : ""}...
            </p>
            <div className="mt-4 space-y-1 text-xs text-slate-500">
              <p>1. Finding real companies that match your search</p>
              <p>2. Reading their public business information</p>
              <p>3. Estimating fit and sales potential</p>
              <p>4. Saving useful prospects to your workspace</p>
            </div>
          </div>
        </Card>
      )}

      {/* Error */}
      {error && <Card className="border-red-400/10 bg-red-400/5"><p role="alert" className="text-sm font-medium text-red-300">Search not completed</p><p className="mt-1 text-xs text-slate-400">{error}</p></Card>}

      {/* Results */}
      {result && (
        <>
          {/* Summary */}
          <Card className="border-emerald-400/10 bg-emerald-400/5">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <div>
                <p className="text-sm font-medium text-white">Discovery complete</p>
                <p className="text-xs text-slate-500">
                  Added {result.leads_created} new {result.leads_created === 1 ? "company" : "companies"}{result.duplicates_skipped ? ` and skipped ${result.duplicates_skipped} already in your CRM` : ""}. Completed in {(result.total_time_ms / 1000).toFixed(1)}s. {" "}
                  <Link href="/leads/workspace" className="text-cyan-400 hover:underline">
                    View in Workspace
                  </Link>
                </p>
              </div>
            </div>
          </Card>

          {/* Company Cards */}
          <div className="space-y-3">
            {result.companies.map((c, i) => (
              <Card key={i}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-white">{c.name}</h3>
                      <Badge variant={c.opportunity_score >= 70 ? "success" : c.opportunity_score >= 50 ? "warning" : "neutral"}>
                        Score: {c.opportunity_score}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400">{c.industry}{c.city ? ` · ${c.city}, ${c.province}` : ""}{c.employees ? ` · ~${c.employees} employees` : ""}</p>
                    {c.executive_summary && (
                      <p className="mt-2 text-xs text-slate-300 leading-relaxed line-clamp-3">{c.executive_summary}</p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                      {c.estimated_deal_low && <span className="text-amber-400 flex items-center gap-1"><TrendingUp className="h-3 w-3" />${c.estimated_deal_low.toLocaleString()}{c.estimated_deal_high ? `-$${c.estimated_deal_high.toLocaleString()}` : ""}</span>}
                      {c.technology_maturity && <span className="text-slate-500">Tech: {c.technology_maturity}</span>}
                      {c.buying_signals && <span className="text-purple-400 flex items-center gap-1"><Target className="h-3 w-3" />Signals detected</span>}
                    </div>
                    {c.recommended_services && (
                      <p className="mt-2 text-xs text-cyan-400/80">{c.recommended_services}</p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Quick Searches */}
      {!result && !loading && (
        <>
          <Card>
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">Quick Discovery Searches</h4>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {QUICK_SEARCHES.map(q => (
                <button key={q.title} onClick={() => runDiscovery(q.industry, q.city)}
                  className="flex items-center gap-3 rounded-lg border border-white/5 p-3 text-left transition hover:border-cyan-400/30 hover:bg-cyan-400/5">
                  <Search className="h-4 w-4 text-cyan-400 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-white">{q.title}</p>
                    <p className="text-xs text-slate-500">{q.industry}{q.city ? ` · ${q.city}` : ""}</p>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
            <div className="py-8 text-center">
              <Sparkles className="mx-auto h-10 w-10 text-cyan-400" />
              <h3 className="mt-3 text-lg font-semibold text-white">AI Prospect Discovery Engine</h3>
              <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
                Enter search criteria above or click a quick search. The AI will suggest candidate companies
                and create reviewable leads. Only approved leads receive additional AI enrichment.
              </p>
              <p className="mt-2 text-xs text-slate-500">
                Cost control: one discovery request, then one enrichment request per approved lead.
              </p>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
