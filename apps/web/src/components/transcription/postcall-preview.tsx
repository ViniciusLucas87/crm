"use client";

import { useEffect, useState } from "react";
import {
  FileText, CheckSquare, Mail, Brain,
  Loader2, ChevronRight, Copy
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type PostCallData = {
  summary?: string;
  actionItems?: string[];
  followUpEmail?: string;
  proposalSuggestions?: string[];
  knowledgeUpdates?: string[];
  tasks?: { title: string; priority: string; due?: string }[];
};

type Props = {
  transcriptId: number | null;
  callId?: number | null;
};

export function PostCallPreview({ transcriptId, callId }: Props) {
  const [data, setData] = useState<PostCallData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"summary" | "tasks" | "email">("summary");

  useEffect(() => {
    if (!transcriptId) return;
    let cancelled = false;

    async function load() {
      try {
        // Try post-call generate endpoint
        const r = await fetch(`/api/sales-coach/postcall/generate/${transcriptId}`, { method: "POST" });
        if (r.ok) {
          const d = await r.json();
          if (!cancelled) {
            setData({
              summary: d.summary || d.report?.summary,
              actionItems: d.action_items || d.report?.action_items || [],
              followUpEmail: d.follow_up_email || d.report?.follow_up_email,
              proposalSuggestions: d.proposal_suggestions || d.report?.proposal_suggestions || [],
              knowledgeUpdates: d.knowledge_updates || [],
              tasks: d.tasks || [],
            });
          }
        }
      } catch {
        // Fallback: try debrief endpoint
        try {
          if (callId) {
            const r = await fetch(`/api/ai/call-debrief/${callId}`, { method: "POST" });
            if (r.ok) {
              const d = await r.json();
              if (!cancelled) setData({
                summary: d.summary,
                actionItems: d.tasks?.map((t: { title: string }) => t.title),
                tasks: d.tasks,
              });
            }
          }
        } catch { /* best effort */ }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [transcriptId, callId]);

  if (!transcriptId || (!loading && !data)) return null;

  return (
    <Card className="bg-gray-900 border-gray-700 overflow-hidden animate-in fade-in slide-in-from-bottom-4">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-gray-700/50 bg-gradient-to-r from-emerald-900/20 to-transparent">
        <Brain className="w-4 h-4 text-emerald-400" />
        <h3 className="text-sm font-semibold text-gray-200">Post-Call Intelligence</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-400/10 text-emerald-400 ml-auto">AI GENERATED</span>
      </div>

      {loading ? (
        <div className="p-6 flex flex-col items-center gap-3">
          <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
          <p className="text-xs text-gray-500">Generating post-call insights...</p>
        </div>
      ) : data ? (
        <>
          {/* Tabs */}
          <div className="flex border-b border-gray-700/50">
            {[
              { id: "summary" as const, label: "Summary", icon: FileText },
              { id: "tasks" as const, label: "Tasks", icon: CheckSquare },
              { id: "email" as const, label: "Follow-up", icon: Mail },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium transition ${
                  activeTab === tab.id
                    ? "text-emerald-400 border-b-2 border-emerald-400"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                <tab.icon className="w-3 h-3" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-4 max-h-[400px] overflow-y-auto">
            {activeTab === "summary" && (
              <div className="space-y-3">
                {data.summary && (
                  <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
                    <p className="text-xs text-gray-400 font-medium mb-1">Conversation Summary</p>
                    <p className="text-[13px] text-gray-200 leading-relaxed">{data.summary}</p>
                  </div>
                )}
                {data.actionItems && data.actionItems.length > 0 && (
                  <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
                    <p className="text-xs text-gray-400 font-medium mb-2">Action Items</p>
                    <div className="space-y-1.5">
                      {data.actionItems.slice(0, 5).map((item, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <ChevronRight className="w-3 h-3 text-emerald-400 mt-0.5 shrink-0" />
                          <p className="text-[12px] text-gray-300">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {data.proposalSuggestions && data.proposalSuggestions.length > 0 && (
                  <div className="p-3 rounded-lg bg-purple-400/5 border border-purple-400/10">
                    <p className="text-xs text-purple-400 font-medium mb-2">Proposal Suggestions</p>
                    <div className="space-y-1">
                      {data.proposalSuggestions.slice(0, 3).map((s, i) => (
                        <p key={i} className="text-[12px] text-gray-300">• {s}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === "tasks" && (
              <div className="space-y-2">
                {data.tasks && data.tasks.length > 0 ? (
                  data.tasks.map((task, i) => (
                    <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${
                        task.priority === "high" ? "bg-red-400" : task.priority === "medium" ? "bg-amber-400" : "bg-blue-400"
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] text-gray-200">{task.title}</p>
                        {task.due && <p className="text-[10px] text-gray-500">Due: {task.due}</p>}
                      </div>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                        task.priority === "high" ? "bg-red-400/10 text-red-400" :
                        task.priority === "medium" ? "bg-amber-400/10 text-amber-400" :
                        "bg-blue-400/10 text-blue-400"
                      }`}>{task.priority}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500 text-center py-4">No tasks generated yet.</p>
                )}
              </div>
            )}

            {activeTab === "email" && (
              <div className="space-y-3">
                {data.followUpEmail ? (
                  <>
                    <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
                      <p className="text-xs text-gray-400 font-medium mb-1">Follow-up Email Draft</p>
                      <p className="text-[12px] text-gray-200 leading-relaxed whitespace-pre-wrap">{data.followUpEmail}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(data.followUpEmail || "")}
                      className="w-full text-xs text-gray-400"
                    >
                      <Copy className="w-3 h-3 mr-1" /> Copy to clipboard
                    </Button>
                  </>
                ) : (
                  <p className="text-xs text-gray-500 text-center py-4">Follow-up email will be generated after the call.</p>
                )}
              </div>
            )}
          </div>
        </>
      ) : null}
    </Card>
  );
}
