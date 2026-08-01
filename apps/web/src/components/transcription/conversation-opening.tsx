"use client";

import { useEffect, useState } from "react";
import {
  Lightbulb, Target, MessageSquare, Shield, ChevronRight,
  Phone, Brain
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

type ConversationOpening = {
  iceBreaker: string;
  purposeStatement: string;
  permissionQuestion: string;
  firstDiscoveryQuestion: string;
  suggestedTransition: string;
  confidenceTips: string[];
  companyContext: string;
};

type Props = {
  companyId: number;
  isCallActive: boolean;
  onStartCall?: () => void;
};

export function ConversationOpening({ companyId, isCallActive, onStartCall }: Props) {
  const [opening, setOpening] = useState<ConversationOpening | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isCallActive) return;
    let cancelled = false;

    async function load() {
      try {
        const r = await fetch(`/api/ai/call-prep/${companyId}`);
        if (!r.ok) throw new Error("Failed");
        const data = await r.json();

        if (!cancelled) {
          setOpening({
            iceBreaker: data.company_summary
              ? `I noticed ${data.company_summary.split(".")[0].trim().substring(0, 120)}.`
              : "Thanks for taking the time to connect today.",
            purposeStatement:
              "My goal today isn't to sell anything immediately. I'd like to understand how your current process works and see if there's an opportunity to help.",
            permissionQuestion:
              "Would it be okay if I asked a few questions about how your team currently handles things?",
            firstDiscoveryQuestion:
              data.suggestedQuestions?.[0] ||
              "Can you tell me a bit about your role and what you're responsible for?",
            suggestedTransition:
              "That's really helpful context. Let me ask about something specific...",
            confidenceTips: [
              "Speak at a natural pace — don't rush.",
              "Listen more than you talk — aim for 40/60 split.",
              "Use their name naturally throughout the conversation.",
              "Pause after asking questions — let them fill the silence.",
            ],
            companyContext: data.company_summary || "",
          });
        }
      } catch {
        if (!cancelled) {
          setOpening({
            iceBreaker: "Thanks for taking the time to connect today.",
            purposeStatement:
              "I'd love to understand more about your business and see if there's a way we can help.",
            permissionQuestion:
              "Would it be okay if I asked a few questions to understand your current setup?",
            firstDiscoveryQuestion:
              "Can you walk me through how your team currently handles things?",
            suggestedTransition:
              "That's helpful — let me ask about something specific...",
            confidenceTips: [
              "Speak at a natural pace.",
              "Listen more than you talk.",
              "Use their name naturally.",
            ],
            companyContext: "",
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [companyId, isCallActive]);

  if (isCallActive) return null;
  if (loading) {
    return (
      <Card className="p-6 bg-gray-900 border-gray-700">
        <div className="space-y-4">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </Card>
    );
  }
  if (!opening) return null;

  return (
    <Card className="bg-gray-900 border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-gray-700/50 bg-gradient-to-r from-purple-900/20 to-transparent">
        <Brain className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-semibold text-gray-200">Conversation Opening</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-400/10 text-purple-400 ml-auto">PRE-CALL</span>
      </div>

      <div className="p-5 space-y-4">
        {/* Company Context */}
        {opening.companyContext && (
          <div className="p-3 rounded-lg bg-purple-400/5 border border-purple-400/10">
            <p className="text-[11px] text-purple-400 font-medium mb-1">Company Intelligence</p>
            <p className="text-[12px] text-gray-300 leading-relaxed">{opening.companyContext}</p>
          </div>
        )}

        {/* Ice Breaker */}
        <Section icon={<MessageSquare className="w-3.5 h-3.5" />} label="Ice Breaker" color="text-cyan-400" bg="bg-cyan-400/5" border="border-cyan-400/10">
          <p className="text-[13px] text-gray-200 leading-relaxed italic">&ldquo;{opening.iceBreaker}&rdquo;</p>
        </Section>

        {/* Purpose Statement */}
        <Section icon={<Target className="w-3.5 h-3.5" />} label="Purpose Statement" color="text-emerald-400" bg="bg-emerald-400/5" border="border-emerald-400/10">
          <p className="text-[13px] text-gray-200 leading-relaxed">{opening.purposeStatement}</p>
        </Section>

        {/* Permission Question */}
        <Section icon={<Shield className="w-3.5 h-3.5" />} label="Permission Question" color="text-amber-400" bg="bg-amber-400/5" border="border-amber-400/10">
          <p className="text-[13px] text-gray-200 leading-relaxed italic">&ldquo;{opening.permissionQuestion}&rdquo;</p>
        </Section>

        {/* First Discovery Question */}
        <Section icon={<Lightbulb className="w-3.5 h-3.5" />} label="First Discovery Question" color="text-blue-400" bg="bg-blue-400/5" border="border-blue-400/10">
          <p className="text-[13px] text-gray-200 leading-relaxed font-medium">{opening.firstDiscoveryQuestion}</p>
        </Section>

        {/* Confidence Tips */}
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/50">
          <p className="text-[11px] text-gray-500 font-medium mb-2">Confidence Tips</p>
          <div className="space-y-1.5">
            {opening.confidenceTips.map((tip, i) => (
              <div key={i} className="flex items-start gap-2">
                <ChevronRight className="w-3 h-3 text-gray-600 mt-0.5 shrink-0" />
                <p className="text-[12px] text-gray-400">{tip}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Call Button */}
        {onStartCall && (
          <button
            onClick={onStartCall}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition"
          >
            <Phone className="w-4 h-4" />
            Start Call
          </button>
        )}
      </div>
    </Card>
  );
}

function Section({
  icon, label, color, bg, border, children,
}: {
  icon: React.ReactNode; label: string; color: string; bg: string; border: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`p-3 rounded-lg ${bg} ${border}`}>
      <div className={`flex items-center gap-1.5 mb-1.5 ${color}`}>
        {icon}
        <span className="text-[11px] font-medium">{label}</span>
      </div>
      {children}
    </div>
  );
}
