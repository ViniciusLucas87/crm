"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle, Circle, Clock } from "lucide-react";

type Task = {
  id: number; title: string; description?: string;
  priority: string; status: string; dueDate: string;
  isCompleted: boolean;
};

const PRIORITY_COLORS: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  high: "danger", medium: "warning", low: "neutral",
};

export function CompanyTasksTab({ companyId }: { companyId: number }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = useCallback(async () => {
    try {
      const r = await fetch(`/api/tasks?company_id=${companyId}`);
      const d = await r.json();
      setTasks(d.items || []);
    } finally { setLoading(false); }
  }, [companyId]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  if (loading) return <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-14 rounded-xl" />)}</div>;

  if (tasks.length === 0) {
    return (
      <Card className="border-white/5 bg-slate-800/30 py-10 text-center">
        <Clock className="mx-auto h-8 w-8 text-slate-600 mb-2" />
        <p className="text-sm text-slate-400">No tasks yet.</p>
        <p className="text-xs text-slate-500 mt-1">Create follow-ups and action items for this company.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map(t => (
        <Card key={t.id} className="border-white/5 bg-slate-800/20 p-3 flex items-start gap-3">
          {t.isCompleted ? <CheckCircle className="h-5 w-5 text-emerald-400 mt-0.5 shrink-0" /> : <Circle className="h-5 w-5 text-slate-600 mt-0.5 shrink-0" />}
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium ${t.isCompleted ? "text-slate-500 line-through" : "text-white"}`}>{t.title}</p>
            {t.description && <p className="text-xs text-slate-500 mt-0.5">{t.description}</p>}
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={PRIORITY_COLORS[t.priority] || "neutral"}>{t.priority}</Badge>
              <span className="text-xs text-slate-600">{new Date(t.dueDate).toLocaleDateString()}</span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
