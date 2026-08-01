"use client";

import { useEffect, useState } from "react";
import { Building2, UserPlus, Phone, ClipboardList, Target, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

type TimelineEvent = {
  id: number;
  eventType: string;
  entityType: string;
  title: string;
  description: string | null;
  companyName: string | null;
  occurredAt: string;
};

const iconMap: Record<string, typeof Building2> = {
  company: Building2,
  contact: UserPlus,
  activity: Phone,
  task: ClipboardList,
  opportunity: Target,
};

export function TimelineView({ companyId }: { companyId?: number }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams({ page: "1", page_size: "30" });
    if (companyId) params.set("company_id", String(companyId));
    fetch(`/api/timeline?${params}`)
      .then(r => r.json())
      .then(d => { setEvents(d.items ?? []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [companyId]);

  if (loading) {
    return <div className="space-y-2">{Array.from({length:5}).map((_,i)=><Skeleton key={i} className="h-16 rounded-xl"/>)}</div>;
  }

  if (events.length === 0) {
    return <Card><p className="text-sm text-slate-500 text-center py-8">No events yet. Activity will appear here.</p></Card>;
  }

  return (
    <div className="relative">
      <div className="absolute left-[19px] top-0 h-full w-px bg-white/5" />
      <div className="space-y-1">
        {events.map((event, i) => {
          const Icon = iconMap[event.entityType] ?? Clock;
          const time = new Date(event.occurredAt).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
          return (
            <div key={`${event.entityType}-${event.id}-${i}`} className="relative flex items-start gap-4 py-3 pl-12">
              <div className="absolute left-0 top-3.5 z-10 flex h-[38px] w-[38px] items-center justify-center rounded-full border border-white/10 bg-slate-900 text-slate-400">
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-200">{event.title}</p>
                <p className="text-xs text-slate-400">
                  {event.description && <span>{event.description} &middot; </span>}
                  {event.companyName && <span>{event.companyName} &middot; </span>}
                  {time}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
