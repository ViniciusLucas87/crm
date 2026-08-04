"use client";

import React, { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ToolPage, ContactStep } from "@/components/free-tools/tool-page";
import { ArrowUp, Users } from "lucide-react";
import { track } from "@/lib/analytics";

const SLUG = "crm-readiness-assessment";

/* ------------------------------------------------------------------ */
/*  Questions                                                           */
/* ------------------------------------------------------------------ */

interface Question {
  id: string;
  text: string;
  options: { label: string; score: number; hint?: string }[];
}

const QUESTIONS: Question[] = [
  {
    id: "lead_capture",
    text: "How do you capture new leads today?",
    options: [
      { label: "We don't have a defined process", score: 0 },
      { label: "Email inbox or paper notes", score: 1, hint: "Scattered across inboxes" },
      { label: "Spreadsheet or shared document", score: 2, hint: "Manual, but centralized" },
      { label: "Web forms that go to email", score: 3, hint: "Automated capture, manual routing" },
      { label: "CRM or dedicated lead-capture system", score: 4 },
    ],
  },
  {
    id: "response_time",
    text: "How quickly does your team typically respond to a new lead?",
    options: [
      { label: "More than 48 hours", score: 0 },
      { label: "24–48 hours", score: 1 },
      { label: "Same business day", score: 2 },
      { label: "Within 2 hours during business hours", score: 3 },
      { label: "Under 30 minutes with automation", score: 4 },
    ],
  },
  {
    id: "ownership",
    text: "Is it always clear who owns each lead or customer relationship?",
    options: [
      { label: "No — leads get dropped or double-assigned often", score: 0 },
      { label: "Sometimes — it depends who was available", score: 1 },
      { label: "Mostly — we have informal ownership", score: 2 },
      { label: "Yes — assigned in a shared system", score: 3 },
      { label: "Yes — with automatic assignment and handoff rules", score: 4 },
    ],
  },
  {
    id: "stages",
    text: "Do you track what stage each lead or deal is in?",
    options: [
      { label: "No — everything is in people's heads", score: 0 },
      { label: "We have basic stages: new, working, closed", score: 1 },
      { label: "We track stages in a spreadsheet or whiteboard", score: 2 },
      { label: "We use pipeline stages in a CRM or project tool", score: 3 },
      { label: "We have defined stages with SLAs and automated progression", score: 4 },
    ],
  },
  {
    id: "follow_up",
    text: "How consistent is your follow-up with leads and customers?",
    options: [
      { label: "We rely on memory — reminders are missed", score: 0 },
      { label: "Calendar reminders or sticky notes", score: 1 },
      { label: "Shared task list, some items slip through", score: 2 },
      { label: "CRM tasks or automated reminders", score: 3 },
      { label: "Automated sequences with personal follow-up triggers", score: 4 },
    ],
  },
  {
    id: "data_quality",
    text: "How accurate and complete is your customer and lead data?",
    options: [
      { label: "We don't really track this", score: 0 },
      { label: "Some records have names; most lack details", score: 1 },
      { label: "We have basic info but duplicates and gaps exist", score: 2 },
      { label: "Most records are complete with notes and history", score: 3 },
      { label: "Data is verified, deduplicated, and enriched automatically", score: 4 },
    ],
  },
  {
    id: "reporting",
    text: "Can you answer 'how many deals will close this month' in under a minute?",
    options: [
      { label: "No — we'd need to ask everyone individually", score: 0 },
      { label: "We could guess based on gut feel", score: 1 },
      { label: "We have a spreadsheet that's updated weekly", score: 2 },
      { label: "Yes — we pull a pipeline report from our system", score: 3 },
      { label: "Yes — our dashboard shows real-time pipeline with forecasts", score: 4 },
    ],
  },
  {
    id: "integrations",
    text: "How connected are your customer-facing tools (email, accounting, quoting, scheduling)?",
    options: [
      { label: "Completely separate — lots of copy-paste", score: 0 },
      { label: "A few manual exports/imports between tools", score: 1 },
      { label: "Some tools share data via basic integrations", score: 2 },
      { label: "Most tools are connected through our CRM or middleware", score: 3 },
      { label: "Fully integrated — single source of truth across all tools", score: 4 },
    ],
  },
  {
    id: "privacy",
    text: "How do you manage who can access customer information?",
    options: [
      { label: "Everyone has access to everything", score: 0 },
      { label: "We have shared passwords or accounts", score: 1 },
      { label: "Role-based access in some tools", score: 2 },
      { label: "Defined roles with access policies", score: 3 },
      { label: "Granular permissions, audit logs, and compliance-ready", score: 4 },
    ],
  },
  {
    id: "backups",
    text: "What happens to your customer data if a laptop is lost or a tool stops working?",
    options: [
      { label: "It would be gone — no backups", score: 0 },
      { label: "Some data is in cloud tools but not all", score: 1 },
      { label: "Most data is cloud-based with basic recovery", score: 2 },
      { label: "We have regular backups and can restore within days", score: 3 },
      { label: "Automated backups, tested recovery, business continuity plan", score: 4 },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Scoring                                                             */
/* ------------------------------------------------------------------ */

interface ScoreResult {
  score: number;
  maxScore: number;
  percentage: number;
  band: string;
  bandColor: string;
  nextSteps: string[];
}

function calculateScore(answers: Record<string, number>): ScoreResult {
  const maxScore = QUESTIONS.length * 4;
  const total = Object.values(answers).reduce((sum, v) => sum + v, 0);
  const pct = Math.round((total / maxScore) * 100);

  let band: string;
  let bandColor: string;
  let nextSteps: string[];

  if (pct >= 80) {
    band = "Optimized";
    bandColor = "text-green-700";
    nextSteps = [
      "Your CRM processes are strong. Focus on continuous improvement: advanced automation, AI-assisted insights, and deeper integrations.",
      "Consider a CRM audit to identify edge cases and optimization opportunities.",
      "Document your processes so they scale as your team grows.",
    ];
  } else if (pct >= 60) {
    band = "Developing";
    bandColor = "text-blue-700";
    nextSteps = [
      "You have solid foundations but gaps in consistency and automation.",
      "Focus on: automated lead routing, standardized follow-up sequences, and pipeline reporting.",
      "A CRM consolidation project could connect your existing tools into a single workflow.",
    ];
  } else if (pct >= 35) {
    band = "Foundational";
    bandColor = "text-amber-700";
    nextSteps = [
      "You're managing leads manually. This works at small scale but creates risk as you grow.",
      "Start with: a centralized lead database, defined pipeline stages, and basic follow-up reminders.",
      "Even a simple CRM with email integration can dramatically reduce dropped leads.",
    ];
  } else {
    band = "Starting Out";
    bandColor = "text-pns-assessment-error";
    nextSteps = [
      "Your current processes are likely costing you leads and revenue through inconsistency.",
      "Priority: choose a CRM or lead-management system and migrate all contacts into it.",
      "Define one pipeline with 3-5 stages, assign ownership for every lead, and set follow-up reminders.",
      "Start with a simple shared process, assign every lead, and measure overdue follow-ups against today’s baseline.",
    ];
  }

  return { score: total, maxScore, percentage: pct, band, bandColor, nextSteps };
}

/* ------------------------------------------------------------------ */
/*  Question Step (one question at a time)                              */
/* ------------------------------------------------------------------ */

function QuestionStep({
  qIndex, question, selected, onSelect, onNext, onBack, isLast,
}: {
  qIndex: number;
  question: Question;
  selected: number | null;
  onSelect: (score: number) => void;
  onNext: () => void;
  onBack: () => void;
  isLast: boolean;
}) {
  return (
    <Card className="p-6 md:p-8" variant="elevated">
      <p className="text-[13px] text-pns-text-muted mb-2">
        Question {qIndex + 1} of {QUESTIONS.length}
      </p>
      <h3 className="font-heading font-semibold text-[18px] text-pns-text-primary mb-6">
        {question.text}
      </h3>
      <div className="space-y-3">
        {question.options.map((opt) => (
          <button
            key={opt.score}
            onClick={() => onSelect(opt.score)}
            className={`w-full text-left p-4 rounded-[10px] border transition-colors ${
              selected === opt.score
                ? "border-[#051226] bg-[#051226] text-white"
                : "border-pns-assessment-input-border bg-pns-assessment-input-bg text-pns-text-primary hover:border-[#051226]/30"
            }`}
            aria-pressed={selected === opt.score}
          >
            <span className={`block text-[15px] font-medium ${selected === opt.score ? "text-white" : ""}`}>
              {opt.label}
            </span>
            {opt.hint && (
              <span className={`block text-[13px] mt-1 ${selected === opt.score ? "text-white/70" : "text-pns-text-muted"}`}>
                {opt.hint}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="flex justify-between mt-6">
        {qIndex > 0 ? (
          <Button variant="ghost" onClick={onBack}>Back</Button>
        ) : <div />}
        <Button onClick={onNext} disabled={selected === null}>
          {isLast ? "See my score" : "Next"}
        </Button>
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Assessment flow                                                     */
/* ------------------------------------------------------------------ */

function AssessmentFlow({ onComplete }: { onComplete: (answers: Record<string, number>) => void }) {
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const question = QUESTIONS[qIndex];
  const selected = answers[question.id] ?? null;

  const handleSelect = (score: number) => {
    setAnswers((prev) => ({ ...prev, [question.id]: score }));
  };

  const handleNext = () => {
    if (qIndex < QUESTIONS.length - 1) {
      setQIndex((i) => i + 1);
    } else {
      track("tool_completed", { tool: SLUG });
      onComplete(answers);
    }
  };

  return (
    <QuestionStep
      qIndex={qIndex}
      question={question}
      selected={selected}
      onSelect={handleSelect}
      onNext={handleNext}
      onBack={() => setQIndex((i) => Math.max(0, i - 1))}
      isLast={qIndex === QUESTIONS.length - 1}
    />
  );
}

/* ------------------------------------------------------------------ */
/*  Results                                                             */
/* ------------------------------------------------------------------ */

function Results({ values, onRestart }: { values: Record<string, unknown>; onRestart: () => void }) {
  const answerMap = useMemo(() => {
    const a: Record<string, number> = {};
    for (const q of QUESTIONS) {
      a[q.id] = (values[q.id] as number) ?? 0;
    }
    return a;
  }, [values]);

  const result = calculateScore(answerMap);
  const [showContact, setShowContact] = useState(false);

  return (
    <div className="space-y-6">
      <Card className="p-6 md:p-8 text-center" variant="elevated">
        <div className="w-20 h-20 mx-auto rounded-full bg-pns-soft-blue flex items-center justify-center mb-4">
          <span className={`text-[28px] font-bold ${result.bandColor}`}>
            {result.percentage}
          </span>
        </div>
        <h2 className="font-heading font-bold text-[22px] text-pns-text-primary mb-1">
          Your CRM Readiness Score
        </h2>
        <p className={`font-heading font-semibold text-[18px] ${result.bandColor} mb-4`}>
          {result.band}
        </p>

        {/* Score bar */}
        <div className="h-2 bg-pns-assessment-input-bg rounded-full mb-6 max-w-md mx-auto">
          <div
            className="h-full rounded-full bg-[#051226] transition-all duration-500"
            style={{ width: `${result.percentage}%` }}
          />
        </div>
        <p className="text-[13px] text-pns-text-muted mb-6">
          {result.score} / {result.maxScore} points
        </p>

        <div className="text-left space-y-3">
          <h4 className="font-heading font-semibold text-[16px] text-pns-text-primary">
            Recommended Next Steps
          </h4>
          <ul className="space-y-2">
            {result.nextSteps.map((step, i) => (
              <li key={i} className="flex gap-2 text-[14px] text-pns-text-muted leading-relaxed">
                <ArrowUp className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#051226]" />
                {step}
              </li>
            ))}
          </ul>
        </div>

        <details className="mt-6 text-left group">
          <summary className="text-[14px] text-pns-text-muted cursor-pointer hover:text-pns-text-primary transition-colors">
            How your score was calculated
          </summary>
          <div className="mt-3 space-y-2">
            {QUESTIONS.map((q) => (
              <div key={q.id} className="flex justify-between text-[14px] py-1 border-b border-pns-assessment-input-border">
                <span className="text-pns-text-muted truncate mr-2">{q.text}</span>
                <span className="font-medium text-pns-text-primary flex-shrink-0">
                    {answerMap[q.id] ?? 0} / 4
                </span>
              </div>
            ))}
          </div>
        </details>
      </Card>

      {!showContact && !values.contact_submitted && !values.contact_skipped && (
        <div className="text-center">
          <Button onClick={() => { setShowContact(true); track("contact_started", { tool: SLUG }); }}>
            <Users className="w-4 h-4 mr-2" />
            Get a free CRM readiness review
          </Button>
          <p className="mt-2 text-[13px] text-pns-text-muted">
            Optional — we&apos;ll review your situation and suggest practical next steps.
          </p>
        </div>
      )}

      {showContact && !values.contact_submitted && !values.contact_skipped && (
        <ContactStep
          onNext={(d) => { if (d.contact_submitted) track("lead_submitted", { tool: SLUG }); }}
          values={{ ...values, _toolSlug: SLUG }}
          resultSummary={`CRM Readiness: ${result.percentage}/100 (${result.band}). Q&A: ${QUESTIONS.map((q) => `${q.id}=${answerMap[q.id]}/4`).join(", ")}.`}
        />
      )}

      <div className="text-center">
        <Button variant="ghost" onClick={onRestart}>Retake assessment</Button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main wrapper                                                        */
/* ------------------------------------------------------------------ */

function CRMReadinessWrapper() {
  const [phase, setPhase] = useState<"assess" | "results">("assess");

  if (phase === "assess") {
    return (
      <ToolPage
        config={{
          title: "CRM Readiness Assessment",
          description: "See how prepared your business is for a CRM.",
          slug: SLUG,
          steps: [
            ({ onNext }: { onNext: (d: Record<string, unknown>) => void }) => (
              <AssessmentFlow
                onComplete={(a) => {
                  onNext(a);
                }}
              />
            ),
          ],
          results: ({ values, onRestart }: { values: Record<string, unknown>; onRestart: () => void }) => (
            <Results
              values={values}
              onRestart={() => {
                setPhase("assess");
                onRestart();
              }}
            />
          ),
        }}
      />
    );
  }

  return null;
}

export default function CRMReadinessPage() {
  React.useEffect(() => { track("tool_view", { tool: SLUG }); }, []);
  return <CRMReadinessWrapper />;
}
