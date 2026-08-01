"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Edit3, Sparkles, Copy, Check } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AiPageNav, AiPageError } from "@/components/ai/ai-page-nav";

type PSection = { heading: string; body: string; editable: boolean };
type Draft = { companyName: string; title: string; sections: PSection[] };

export default function ProposalBuilderPage() {
  const { id } = useParams<{ id: string }>();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Record<number, string>>({});
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch(`/api/ai/proposal/${id}`).then(r => r.ok ? r.json() : Promise.reject(r)).then((d: Record<string, unknown>) => setDraft({
      companyName: d.company_name as string, title: d.title as string,
      sections: (d.sections as Record<string, unknown>[] || []).map(s => ({ heading: s.heading as string, body: s.body as string, editable: s.editable as boolean })),
    })).catch(() => setDraft(null)).finally(() => setLoading(false));
  }, [id]);

  const copyAll = async () => {
    if (!draft) return;
    const text = draft.sections.map(s => `## ${s.heading}\n\n${s.body}`).join("\n\n---\n\n");
    await navigator.clipboard.writeText(text);
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <div className="space-y-2"><AiPageNav companyId={id} pageTitle="Proposal Builder" /><div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div></div>;
  if (!draft) return <AiPageError message="Failed to generate proposal. The company may not exist." companyId={id} />;

  return (
    <div className="space-y-6">
      <AiPageNav companyName={draft.companyName} companyId={id} pageTitle="Proposal Builder" />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Proposal Builder</p>
          <h2 className="mt-1 text-lg font-semibold text-white">{draft.title}</h2>
        </div>
        <Button variant="secondary" onClick={copyAll}>{copied ? <Check className="mr-1 h-3.5 w-3.5" /> : <Copy className="mr-1 h-3.5 w-3.5" />}{copied ? "Copied" : "Copy All"}</Button>
      </div>

      <div className="space-y-4">
        {draft.sections.map((s, i) => (
          <Card key={i}>
            <div className="mb-3 flex items-center gap-2">
              <Edit3 className="h-3.5 w-3.5 text-cyan-400" />
              <p className="text-sm font-semibold text-white">{s.heading}</p>
            </div>
            {editing[i] !== undefined ? (
              <div>
                <textarea className="w-full rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-200 focus:border-cyan-400/50 focus:outline-none" rows={6} value={editing[i]} onChange={e => setEditing({ ...editing, [i]: e.target.value })} />
                <div className="mt-2 flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setEditing(prev => { const n = { ...prev }; delete n[i]; return n; })}>Done</Button>
                </div>
              </div>
            ) : (
              <div>
                <p className="text-sm text-slate-300 whitespace-pre-line">{editing[i] ?? s.body}</p>
                <button onClick={() => setEditing({ ...editing, [i]: s.body })} className="mt-2 text-xs text-cyan-400 transition hover:text-cyan-300">Edit this section</button>
              </div>
            )}
          </Card>
        ))}
      </div>

      <Card className="border-cyan-400/10 bg-cyan-400/5">
        <div className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-cyan-400" /><p className="text-sm text-slate-400">This is an AI-generated draft. All sections are editable. Review and customize before sending to the client.</p></div>
      </Card>
    </div>
  );
}
