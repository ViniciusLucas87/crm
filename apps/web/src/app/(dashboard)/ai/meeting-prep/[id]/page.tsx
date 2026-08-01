"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CalendarCheck2, Target, Lightbulb, Shield, MessageSquare, CheckSquare, TrendingUp, Phone } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AiPageNav, AiPageError } from "@/components/ai/ai-page-nav";

type Section = { title: string; content: string; items: string[] };

export default function MeetingPrepPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<Record<string, Section> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/ai/meeting-prep/${id}`).then(r => r.ok ? r.json() : Promise.reject(r)).then((d: Record<string, unknown>) => {
      const map: Record<string, Section> = {};
      for (const [k, v] of Object.entries(d)) {
        if (typeof v === "object" && v && "title" in v) {
          const sv = v as Record<string, unknown>;
          map[k] = { title: sv.title as string, content: sv.content as string, items: sv.items as string[] || [] };
        }
      }
      setData(map);
    }).catch(() => setData(null)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="space-y-2"><AiPageNav companyId={id} pageTitle="Meeting Preparation" /><div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div></div>;
  if (!data) return <AiPageError message="Failed to load meeting preparation. The company may not exist or the service is unavailable." companyId={id} />;

  const icons: Record<string, typeof CalendarCheck2> = {
    company_overview: CalendarCheck2, recent_timeline: TrendingUp, buying_signals: TrendingUp,
    technology: Phone, research: Lightbulb, contacts: Phone, activities: CalendarCheck2,
    open_opportunities: Target, recommended_goals: Target, suggested_questions: MessageSquare,
    likely_objections: Shield, talking_points: Lightbulb, suggested_opening: MessageSquare,
    suggested_closing: MessageSquare, cross_selling: TrendingUp, upselling: TrendingUp, checklist: CheckSquare,
  };

  const renderSection = (key: string, s: Section) => {
    const Icon = icons[key] || Lightbulb;
    return (
      <Card key={key}>
        <div className="mb-3 flex items-center gap-2">
          <Icon className="h-3.5 w-3.5 text-cyan-400" />
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{s.title}</p>
        </div>
        {s.items.length > 0 ? (
          <ul className="space-y-1.5">
            {s.items.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-cyan-400/60" />
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-200 whitespace-pre-line">{s.content}</p>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <AiPageNav companyName={data.company_name?.title?.split('\n')[0]} companyId={id} pageTitle="Meeting Preparation" />
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Meeting Preparation</p>
      <div className="grid gap-4 lg:grid-cols-2">
        {data.company_overview && renderSection("company_overview", data.company_overview)}
        {data.recent_timeline && renderSection("recent_timeline", data.recent_timeline)}
        {data.buying_signals && renderSection("buying_signals", data.buying_signals)}
        {data.technology && renderSection("technology", data.technology)}
        {data.research && renderSection("research", data.research)}
        {data.contacts && renderSection("contacts", data.contacts)}
        {data.activities && renderSection("activities", data.activities)}
        {data.open_opportunities && renderSection("open_opportunities", data.open_opportunities)}
        {data.recommended_goals && renderSection("recommended_goals", data.recommended_goals)}
        {data.suggested_questions && renderSection("suggested_questions", data.suggested_questions)}
        {data.likely_objections && renderSection("likely_objections", data.likely_objections)}
        {data.talking_points && renderSection("talking_points", data.talking_points)}
      </div>
      {data.suggested_opening && renderSection("suggested_opening", data.suggested_opening)}
      {data.suggested_closing && renderSection("suggested_closing", data.suggested_closing)}
      <div className="grid gap-4 lg:grid-cols-2">
        {data.cross_selling && renderSection("cross_selling", data.cross_selling)}
        {data.upselling && renderSection("upselling", data.upselling)}
      </div>
      {data.checklist && renderSection("checklist", data.checklist)}
    </div>
  );
}
