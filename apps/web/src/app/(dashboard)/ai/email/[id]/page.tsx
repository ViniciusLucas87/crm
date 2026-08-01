"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Copy, Check, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AiPageNav, AiPageError } from "@/components/ai/ai-page-nav";

const TYPES = [
  { id: "cold", label: "Cold Email" },
  { id: "followup", label: "Follow-up" },
  { id: "proposal", label: "Proposal Delivery" },
  { id: "meeting", label: "Meeting Confirmation" },
  { id: "reengagement", label: "Re-engagement" },
  { id: "thank_you", label: "Thank You" },
  { id: "reminder", label: "Reminder" },
  { id: "discovery", label: "Discovery Email" },
];

export default function EmailAssistantPage() {
  const { id } = useParams<{ id: string }>();
  const [emailType, setEmailType] = useState("cold");
  const [data, setData] = useState<{ type: string; subject: string; body: string; companyName?: string; contactName?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const fetchEmail = (type: string) => {
    setLoading(true); setEmailType(type);
    fetch(`/api/ai/email/${id}?email_type=${type}`).then(r => r.ok ? r.json() : Promise.reject(r)).then((d: Record<string, unknown>) => setData({
      type: d.type as string, subject: d.subject as string, body: d.body as string,
      companyName: d.company_name as string, contactName: d.contact_name as string,
    })).catch(() => setData(null)).finally(() => setLoading(false));
  };

  useEffect(() => { fetchEmail("cold"); }, [id]); // eslint-disable-line

  if (loading) return <div className="space-y-2"><AiPageNav companyId={id} pageTitle="Email Assistant" /><Skeleton className="h-64 rounded-xl" /></div>;
  if (!data) return <AiPageError message="Failed to generate email." companyId={id} />;

  const copy = async () => {
    if (!data) return;
    await navigator.clipboard.writeText(`Subject: ${data.subject}\n\n${data.body}`);
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <AiPageNav companyName={data.companyName} companyId={id} pageTitle="Email Assistant" />
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">AI Email Assistant</p>
        <p className="mt-1 text-sm text-slate-400">Generate context-aware email drafts. Edit before sending.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {TYPES.map(t => (
          <button key={t.id} onClick={() => fetchEmail(t.id)} className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${emailType === t.id ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-300" : "border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-300"}`}>{t.label}</button>
        ))}
      </div>

      {loading ? <Skeleton className="h-64 rounded-xl" /> : data ? (
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs text-slate-500">To: {data.contactName || "Contact"} · Company: {data.companyName || "N/A"}</p>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => fetchEmail(emailType)}><RefreshCw className="mr-1 h-3 w-3" />Regenerate</Button>
              <Button size="sm" variant="secondary" onClick={copy}>{copied ? <Check className="mr-1 h-3 w-3" /> : <Copy className="mr-1 h-3 w-3" />}{copied ? "Copied" : "Copy"}</Button>
            </div>
          </div>
          <div className="mb-4 rounded-xl border border-white/10 bg-white/5 px-4 py-2">
            <p className="text-xs text-slate-500">Subject: <span className="text-slate-200">{data.subject}</span></p>
          </div>
          <textarea className="w-full min-h-[300px] rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200 focus:border-cyan-400/50 focus:outline-none" value={data.body} onChange={e => setData({ ...data, body: e.target.value })} />
        </Card>
      ) : <Card><p className="text-red-400">Failed to generate email.</p></Card>}
    </div>
  );
}
