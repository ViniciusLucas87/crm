"use client";

import { useEffect, useState } from "react";
import { BookOpen, Database, FileText, Lightbulb, Shield } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

type Category = { id: string; name: string; description: string; itemCount: number; status: string };

export default function KnowledgeBasePage() {
  const [data, setData] = useState<{ categories: Category[]; totalItems: number; readyForAi: boolean; message: string; mcpSchema: Record<string, unknown> } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/ai/knowledge-base").then(r => r.ok ? r.json() : Promise.reject(r)).then((d: Record<string, unknown>) => {
      const ov = d.overview as Record<string, unknown>;
      setData({
        categories: (ov.categories as Record<string, unknown>[] || []).map(c => ({ id: c.id as string, name: c.name as string, description: c.description as string, itemCount: c.item_count as number, status: c.status as string })),
        totalItems: ov.total_items as number, readyForAi: ov.ready_for_ai as boolean, message: ov.message as string,
        mcpSchema: d.mcp_schema as Record<string, unknown>,
      });
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Knowledge Base</p>
        <h2 className="mt-1 text-lg font-semibold text-white">Internal Knowledge System</h2>
      </div>

      {data && (
        <Card className="border-cyan-400/10 bg-cyan-400/5">
          <div className="flex items-start gap-3">
            <Lightbulb className="mt-1 h-5 w-5 text-cyan-400" />
            <p className="text-sm text-slate-300">{data.message}</p>
          </div>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {(data?.categories || []).map(c => (
          <Card key={c.id}>
            <div className="mb-2 flex items-center gap-2">
              {c.id === "services" ? <Database className="h-4 w-4 text-cyan-400" /> :
               c.id === "pricing" ? <Shield className="h-4 w-4 text-cyan-400" /> :
               c.id === "case_studies" ? <FileText className="h-4 w-4 text-cyan-400" /> :
               <BookOpen className="h-4 w-4 text-cyan-400" />}
              <p className="text-sm font-medium text-white">{c.name}</p>
            </div>
            <p className="text-xs text-slate-400">{c.description}</p>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="neutral">{c.status}</Badge>
              <span className="text-xs text-slate-600">{c.itemCount} items</span>
            </div>
          </Card>
        ))}
      </div>

      {data?.mcpSchema && (() => {
        const schema = data.mcpSchema as Record<string, unknown>;
        const contexts = (schema.contexts || schema) as Record<string, Record<string, unknown>>;
        return (
        <Card>
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">MCP Context Schema (Future AI Agent Integration)</p>
          <div className="mt-3 space-y-2">
            {Object.entries(contexts).filter(([, v]) => typeof v === 'object' && v !== null).map(([key, val]) => (
              <div key={key} className="rounded-lg border border-white/5 bg-white/[0.01] p-3">
                <p className="text-sm font-medium text-cyan-300">{key}</p>
                <p className="text-xs text-slate-400">Source: {val.source as string || 'N/A'} · Fields: {Array.isArray(val.fields) ? (val.fields as string[]).join(", ") : 'N/A'}</p>
              </div>
            ))}
          </div>
        </Card>
        );
      })()}
    </div>
  );
}
