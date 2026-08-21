"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle, Circle, Clock, Plus } from "lucide-react";
import { createTask, listTasks } from "@/lib/api";
import type { Task, TaskCreateInput } from "@/lib/types";

const PRIORITY_COLORS: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  high: "danger", medium: "warning", low: "neutral",
};

export function CompanyTasksTab({ companyId }: { companyId: number }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [taskDraft, setTaskDraft] = useState({ title: "", description: "", dueDate: new Date().toISOString().slice(0, 10), priority: "medium" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await listTasks(companyId);
      setTasks(data.items);
    } finally { setLoading(false); }
  }, [companyId]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const addTask = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!taskDraft.title.trim() || !taskDraft.dueDate) return;

    setSaving(true);
    setError(null);
    try {
      const input: TaskCreateInput = {
        companyId,
        title: taskDraft.title.trim(),
        description: taskDraft.description.trim() || undefined,
        dueDate: taskDraft.dueDate,
        priority: taskDraft.priority,
      };
      const task = await createTask(input);
      setTasks(current => [task, ...current]);
      setTaskDraft(current => ({ ...current, title: "", description: "", priority: "medium" }));
    } catch {
      setError("The task could not be saved. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-14 rounded-xl" />)}</div>;

  return (
    <div className="space-y-3">
      <Card className="border-white/5 bg-slate-800/30 p-4">
        <form className="space-y-3" onSubmit={addTask}>
          <div className="flex items-center gap-2 text-sm font-medium text-white">
            <Plus className="h-4 w-4 text-cyan-300" />
            Add follow-up
          </div>
          <input
            className="w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-sm text-white placeholder:text-slate-500"
            onChange={event => setTaskDraft(current => ({ ...current, title: event.target.value }))}
            placeholder="Call back, send quote, or review next step"
            required
            value={taskDraft.title}
          />
          <textarea
            className="min-h-20 w-full rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-sm text-white placeholder:text-slate-500"
            onChange={event => setTaskDraft(current => ({ ...current, description: event.target.value }))}
            placeholder="Context for the follow-up"
            value={taskDraft.description}
          />
          <div className="flex flex-wrap gap-2">
            <input
              className="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-sm text-white"
              onChange={event => setTaskDraft(current => ({ ...current, dueDate: event.target.value }))}
              required
              type="date"
              value={taskDraft.dueDate}
            />
            <select
              className="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-sm text-white"
              onChange={event => setTaskDraft(current => ({ ...current, priority: event.target.value }))}
              value={taskDraft.priority}
            >
              <option value="low">Low priority</option>
              <option value="medium">Medium priority</option>
              <option value="high">High priority</option>
            </select>
            <button
              className="rounded-lg bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={saving}
              type="submit"
            >
              {saving ? "Saving..." : "Add task"}
            </button>
          </div>
          {error && <p className="text-xs text-rose-300">{error}</p>}
        </form>
      </Card>
      {tasks.length === 0 && (
        <Card className="border-white/5 bg-slate-800/30 py-8 text-center">
          <Clock className="mx-auto mb-2 h-8 w-8 text-slate-600" />
          <p className="text-sm text-slate-400">No tasks yet.</p>
          <p className="mt-1 text-xs text-slate-500">Create follow-ups and action items for this company.</p>
        </Card>
      )}
      {tasks.map(t => (
        <Card key={t.id} className="border-white/5 bg-slate-800/20 p-3 flex items-start gap-3">
          {t.isCompleted ? <CheckCircle className="h-5 w-5 text-emerald-400 mt-0.5 shrink-0" /> : <Circle className="h-5 w-5 text-slate-600 mt-0.5 shrink-0" />}
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium ${t.isCompleted ? "text-slate-500 line-through" : "text-white"}`}>{t.title}</p>
            {t.description && <p className="text-xs text-slate-500 mt-0.5">{t.description}</p>}
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={PRIORITY_COLORS[t.priority] || "neutral"}>{t.priority}</Badge>
              {t.dueDate && (
                <span className="text-xs text-slate-600">{new Date(t.dueDate).toLocaleDateString()}</span>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
