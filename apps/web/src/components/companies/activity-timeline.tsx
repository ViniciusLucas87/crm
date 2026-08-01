"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { listActivities, createActivity } from "@/lib/api";
import type { Activity, ActivityCreateInput } from "@/lib/types";

// ── Icons per type ──
const TYPE_ICONS: Record<string, string> = {
  call: "📞",
  email: "✉️",
  meeting: "🤝",
  note: "📝",
  follow_up: "⏰",
};

const TYPE_LABELS: Record<string, string> = {
  call: "Call",
  email: "Email",
  meeting: "Meeting",
  note: "Note",
  follow_up: "Follow-up",
};

// ═══════════════════════════════════════════════════════════
// ACTIVITY MODAL
// ═══════════════════════════════════════════════════════════

function ActivityModal({
  open,
  onClose,
  companyId,
  defaultType,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  companyId: number;
  defaultType: string;
  onSaved: () => void;
}) {
  const [activityType, setActivityType] = useState(defaultType);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { setActivityType(defaultType); }, [defaultType]);

  // Handle Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const handleSave = async () => {
    if (!subject.trim() || !body.trim()) {
      setError("Subject and notes are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const input: ActivityCreateInput = {
        companyId,
        activityType,
        subject: subject.trim(),
        body: body.trim(),
      };
      await createActivity(input);
      setSubject("");
      setBody("");
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save activity.");
    } finally {
      setSaving(false);
    }
  };

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl" onClick={e => e.stopPropagation()} onKeyDown={() => {}} role="presentation">
        <h3 className="text-lg font-semibold text-white mb-4">
          Log {TYPE_LABELS[activityType] || "Activity"}
        </h3>

        <div className="space-y-4">
          <div>
            <label htmlFor="activity-type" className="text-xs text-slate-500 mb-1 block">Type</label>
            <select
              id="activity-type"
              value={activityType}
              onChange={e => setActivityType(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white"
            >
              {Object.entries(TYPE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="activity-subject" className="text-xs text-slate-500 mb-1 block">Subject *</label>
            <input
              id="activity-subject"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="e.g., Discussed inspection software pilot"
              className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white placeholder:text-slate-600"
            />
          </div>

          <div>
            <label htmlFor="activity-body" className="text-xs text-slate-500 mb-1 block">Notes *</label>
            <textarea
              id="activity-body"
              value={body}
              onChange={e => setBody(e.target.value)}
              placeholder="What was discussed? What are the next steps?"
              rows={4}
              className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white placeholder:text-slate-600 resize-none"
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={onClose}>Cancel</Button>
            <Button variant="primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// ACTIVITY TIMELINE
// ═══════════════════════════════════════════════════════════

export function ActivityTimeline({ companyId }: { companyId: number }) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [defaultType, setDefaultType] = useState("call");

  const fetchActivities = useCallback(async () => {
    try {
      setError("");
      const data = await listActivities(companyId, { pageSize: 50 });
      setActivities(data.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load activities.");
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => { fetchActivities(); }, [fetchActivities]);

  const openModal = (type: string) => {
    setDefaultType(type);
    setModalOpen(true);
  };

  const ACTIVITY_TYPES = ["call", "email", "meeting", "note", "follow_up"] as const;

  return (
    <div className="space-y-4">
      {/* Header + Buttons */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-[0.1em] text-slate-400">CRM Activity</h3>
        <div className="flex gap-1">
          {ACTIVITY_TYPES.map(t => (
            <Button key={t} variant="secondary" size="sm" onClick={() => openModal(t)}>
              {TYPE_ICONS[t]} {TYPE_LABELS[t]}
            </Button>
          ))}
        </div>
      </div>

      {/* Modal */}
      <ActivityModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        companyId={companyId}
        defaultType={defaultType}
        onSaved={fetchActivities}
      />

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <Card className="border-red-400/10 bg-red-400/5">
          <p className="text-sm text-red-400">{error}</p>
        </Card>
      )}

      {/* Empty */}
      {!loading && !error && activities.length === 0 && (
        <Card className="border-white/5 bg-slate-800/30 py-10 text-center">
          <p className="text-sm text-slate-400">No CRM activity has been logged yet.</p>
          <p className="text-xs text-slate-500 mt-1">Start by logging your first interaction.</p>
        </Card>
      )}

      {/* Timeline */}
      {!loading && activities.length > 0 && (
        <div className="space-y-2">
          {activities.map(a => (
            <Card key={a.id} className="border-white/5 bg-slate-800/20 hover:bg-slate-800/30 transition">
              <div className="flex gap-3">
                <span className="text-lg shrink-0 mt-0.5">{TYPE_ICONS[a.activityType] || "📌"}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="neutral">{TYPE_LABELS[a.activityType] || a.activityType}</Badge>
                    <span className="text-xs text-slate-500">
                      {new Date(a.createdAt).toLocaleDateString()} · {new Date(a.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-white mt-1">{a.subject}</p>
                  {a.body && <p className="text-xs text-slate-400 mt-1 leading-relaxed whitespace-pre-line">{a.body}</p>}
                  {a.contactId && <p className="text-xs text-slate-500 mt-1">Contact ID: {a.contactId}</p>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
