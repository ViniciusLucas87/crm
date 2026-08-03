"use client";

import { useState, useEffect } from "react";
import { Check, X, Mail, FileText, ListTodo, AlertTriangle, BarChart3, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type QueueItem = {
  id: string;
  transcript_id: number;
  call_id: number;
  type: string;
  status: string;
  content: string;
  generated_at: string;
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  meeting_summary: <FileText className="w-4 h-4" />,
  action_items: <ListTodo className="w-4 h-4" />,
  follow_up_email: <Mail className="w-4 h-4" />,
  crm_notes: <FileText className="w-4 h-4" />,
  tasks: <ListTodo className="w-4 h-4" />,
  risk_assessment: <AlertTriangle className="w-4 h-4" />,
  deal_score: <BarChart3 className="w-4 h-4" />,
  next_steps: <ArrowRight className="w-4 h-4" />,
};

const TYPE_LABELS: Record<string, string> = {
  meeting_summary: "Meeting Summary",
  action_items: "Action Items",
  follow_up_email: "Follow-up Email",
  crm_notes: "CRM Notes",
  tasks: "Tasks",
  risk_assessment: "Risk Assessment",
  deal_score: "Deal Score",
  next_steps: "Next Steps",
};

export function PostCallQueue() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const r = await fetch("/api/sales-coach/postcall/queue");
      const d = await r.json();
      setItems(d.items || []);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleApprove = async (itemId: string) => {
    await fetch(`/api/sales-coach/postcall/queue/${itemId}/approve`, { method: "POST" });
    setItems(prev => prev.map(i => i.id === itemId ? { ...i, status: "approved" } : i));
  };

  const handleReject = async (itemId: string) => {
    await fetch(`/api/sales-coach/postcall/queue/${itemId}/reject`, { method: "POST" });
    setItems(prev => prev.map(i => i.id === itemId ? { ...i, status: "rejected" } : i));
  };

  const pending = items.filter(i => i.status === "pending");

  if (pending.length === 0 && !loading) {
    return null;
  }

  return (
    <Card className="fixed bottom-4 right-4 z-40 flex max-h-[70vh] w-96 flex-col bg-gray-900 border-gray-700 shadow-2xl">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Approval Queue</h3>
        <span className="text-[10px] text-gray-400">{pending.length} pending</span>
      </div>

      <div className="divide-y divide-gray-700 max-h-[500px] overflow-y-auto">
        {pending.map((item) => (
          <div key={item.id} className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-gray-400">{TYPE_ICONS[item.type]}</span>
                <span className="text-xs font-medium text-gray-200">{TYPE_LABELS[item.type] || item.type}</span>
              </div>
              <span className="text-[9px] text-gray-500">{new Date(item.generated_at).toLocaleTimeString()}</span>
            </div>

            <div className="text-xs text-gray-300 bg-gray-800 rounded-lg p-3 max-h-32 overflow-y-auto whitespace-pre-wrap">
              {item.content}
            </div>

            <div className="flex items-center gap-2">
              <Button
                onClick={() => handleApprove(item.id)}
                className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded-lg"
              >
                <Check className="w-3 h-3" /> Approve
              </Button>
              <Button
                onClick={() => handleReject(item.id)}
                className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs px-3 py-1.5 rounded-lg"
              >
                <X className="w-3 h-3" /> Reject
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
