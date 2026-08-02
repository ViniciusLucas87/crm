"use client";

import { useEffect, useRef, useState } from "react";
import {
  Navigation, Zap, Brain, Loader2, Activity, Ear, Users,
  Check, X, RefreshCw, ChevronDown, ChevronUp,
  SkipForward, ArrowRight, ArrowLeft, Play,
} from "lucide-react";
import type { TranscriptSegment } from "@/lib/transcription";

type GPSData = {
  current_destination?: string; destination_key?: string;
  next_milestone?: string; recommended_route?: string[];
  progress_pct?: number; completed_count?: number; total_count?: number;
  stages?: { key: string; label: string; status: string }[];
};

type Recommendation = {
  priority?: string; key?: string; title?: string;
  detail?: string; action?: string; suggested_wording?: string;
  reason?: string; evidence?: string; expected_outcome?: string;
  alternatives?: string[]; transition?: string; expires_when?: string;
  confidence?: number;
  source?: string; partial?: boolean; category?: string; stage?: string;
  based_on_segment?: number; relevance_version?: number; created_at?: number;
};

type DealHealth = {
  discovery_quality?: number; buying_intent?: number;
  close_probability?: number;
};

type FastCoachState = {
  stage?: string; talk_ratio?: number;
  agent_words?: number; prospect_words?: number;
  agent_utterances?: number; prospect_utterances?: number;
  segments_processed?: number; discovered?: string[];
  both_channels_live?: boolean; grace_period_active?: boolean;
};

type Props = {
  callId: string | number | null;
  isCallActive: boolean;
  segments: TranscriptSegment[];
  /** Pre-call intelligence for the opening script */
  preCall?: {
    companyName?: string;
    companySummary?: string;
    suggestedQuestions?: string[];
    talkingPoints?: string[];
    objectives?: { goal: string; successCriteria: string }[];
  };
  contacts?: { firstName?: string; lastName?: string; jobTitle?: string | null }[];
};

/** Semantic status for the coach panel — never blank, always informative */
type CoachStatus = 
  | "connecting"
  | "listening"
  | "identifying_question"
  | "updating_discovery"
  | "checking_objections"
  | "preparing_recommendation"
  | "ai_refining"
  | "ready";

const STATUS_LABELS: Record<CoachStatus, { label: string; icon: React.ReactNode }> = {
  connecting: { label: "Connecting to coach…", icon: <Loader2 className="w-4 h-4 animate-spin text-gray-400" /> },
  listening: { label: "Listening to prospect", icon: <Ear className="w-4 h-4 text-cyan-400 animate-pulse" /> },
  identifying_question: { label: "Identifying next question", icon: <Activity className="w-4 h-4 text-purple-400" /> },
  updating_discovery: { label: "Updating discovery", icon: <Activity className="w-4 h-4 text-emerald-400" /> },
  checking_objections: { label: "Checking for objections", icon: <Activity className="w-4 h-4 text-amber-400" /> },
  preparing_recommendation: { label: "Preparing recommendation", icon: <Activity className="w-4 h-4 text-purple-400" /> },
  ai_refining: { label: "AI refining…", icon: <Loader2 className="w-4 h-4 animate-spin text-purple-400" /> },
  ready: { label: "Ready", icon: <Zap className="w-4 h-4 text-emerald-400" /> },
};

// ═══════════════════════════════════════════════════════════
// OPENING SCRIPT SYSTEM
// ═══════════════════════════════════════════════════════════

type ScriptStep = {
  id: string;
  line: string;                    // The line the seller says
  note?: string;                   // Optional stage direction
  expectedResponse?: string;       // What the prospect might say
  isQuestion: boolean;            // This line expects a response
};

type ResponseBranch = {
  id: string;
  label: string;                   // "Yes", "No", "Busy", etc.
  matchKeywords: string[];        // Keywords that trigger this branch
  nextSteps: ScriptStep[];        // What to say after this response
};

type OpeningScript = {
  id: string;
  name: string;
  version: string;
  callType: "cold_outbound" | "referral" | "assessment_followup" | "proposal_followup";
  objective: string;
  steps: ScriptStep[];
  branches: Record<string, ResponseBranch>;
  firstDiscoveryQuestions: string[];
  meetingClose: { wording: string; alternatives: string[] };
  assessmentClose: { wording: string; alternatives: string[] };
};

const DEFAULT_OPENING_SCRIPT: OpeningScript = {
  id: "pns-assessment-cold",
  name: "PNS Business Efficiency Assessment",
  version: "1.0",
  callType: "cold_outbound",
  objective: "assessment_conversion",
  steps: [
    { id: "intro_hi", line: "Hi {name}.", isQuestion: false },
    { id: "intro_name", line: "My name is Vini.", isQuestion: false },
    { id: "intro_company", line: "I'm calling from Pacific North Systems here in Vancouver.", isQuestion: false },
    { id: "qualify", line: "Quick question — are you the person responsible for improving operations or technology in the company?", isQuestion: true, expectedResponse: "Yes / No / Partially / Busy / Not interested" },
  ],
  branches: {
    yes: {
      id: "yes", label: "Yes", matchKeywords: ["yes", "i am", "that's me", "correct", "right", "speaking"],
      nextSteps: [
        { id: "yes_ack", line: "Perfect.", isQuestion: false },
        { id: "yes_pitch1", line: "We're reaching out to local businesses because we've built a free Business Efficiency Assessment.", isQuestion: false },
        { id: "yes_pitch2", line: "It helps identify where companies may be losing time through repetitive administrative work, manual processes, or disconnected systems.", isQuestion: false },
        { id: "yes_pitch3", line: "It usually takes around eight to ten minutes.", isQuestion: false },
        { id: "yes_ask", line: "Would you be open to taking a look?", isQuestion: true, expectedResponse: "Yes / Busy / Send link / Not now" },
      ],
    },
    no: {
      id: "no", label: "No", matchKeywords: ["no", "not me", "not sure", "someone else", "different person"],
      nextSteps: [
        { id: "no_ack", line: "No problem. Who would normally be responsible for operations improvement, internal systems, or technology decisions?", isQuestion: true, expectedResponse: "Name / Department" },
        { id: "no_ask", line: "Would you be able to point me in the right direction or share the best way to contact them?", isQuestion: true, expectedResponse: "Contact info" },
      ],
    },
    partially: {
      id: "partially", label: "Partially", matchKeywords: ["partially", "some of", "part of", "kind of", "sort of"],
      nextSteps: [
        { id: "part_ack", line: "Understood. Which parts of operations or technology are you involved with?", isQuestion: true, expectedResponse: "Description of role" },
        { id: "part_then", line: "Perfect. We're reaching out to local businesses because we've built a free Business Efficiency Assessment.", isQuestion: false },
        { id: "part_ask", line: "Would you be open to taking a look?", isQuestion: true, expectedResponse: "Yes / Busy / Not now" },
      ],
    },
    busy: {
      id: "busy", label: "Busy", matchKeywords: ["busy", "don't have time", "in a meeting", "call back", "quick"],
      nextSteps: [
        { id: "busy_ack", line: "Of course. I'll keep it brief.", isQuestion: false },
        { id: "busy_pitch", line: "The assessment helps identify repetitive work and potential automation opportunities.", isQuestion: false },
        { id: "busy_ask", line: "Would it be better if I sent you the link, or should we schedule a short time to review it together?", isQuestion: true, expectedResponse: "Send link / Schedule call" },
      ],
    },
    not_interested: {
      id: "not_interested", label: "Not interested", matchKeywords: ["not interested", "don't need", "no thanks", "we're good", "not relevant"],
      nextSteps: [
        { id: "ni_ack", line: "Understood — no pressure at all.", isQuestion: false },
        { id: "ni_ask", line: "Before I let you go, is that because improving operations is not a priority right now, or because the assessment itself is not relevant?", isQuestion: true, expectedResponse: "Objection reason" },
      ],
    },
    what_is_pns: {
      id: "what_is_pns", label: "Asks what PNS does", matchKeywords: ["what do you do", "who are you", "what is pacific", "what's pacific", "your company"],
      nextSteps: [
        { id: "pns_desc", line: "We build practical software and automation for businesses that want to reduce repetitive work, connect disconnected systems, and improve operational workflows.", isQuestion: false },
        { id: "pns_return", line: "Would you be open to taking a look at the assessment?", isQuestion: true, expectedResponse: "Yes / No" },
      ],
    },
    assessment_yes: {
      id: "assessment_yes", label: "Accepts assessment", matchKeywords: ["yes", "sure", "okay", "send it", "i'll take", "let's do it"],
      nextSteps: [
        { id: "as_ack", line: "Perfect. I can send you the assessment link now.", isQuestion: false },
        { id: "as_detail", line: "It takes about eight to ten minutes, and once you complete it, you'll receive a summary of your biggest automation opportunities.", isQuestion: false },
        { id: "as_mode", line: "Would you prefer to complete it on your own, or schedule a short call where we can review the results together?", isQuestion: true, expectedResponse: "Own / Schedule call" },
      ],
    },
    send_link: {
      id: "send_link", label: "Wants link sent", matchKeywords: ["send", "email", "link", "later", "on my own"],
      nextSteps: [
        { id: "sl_ack", line: "Perfect — I'll send that right over.", isQuestion: false },
        { id: "sl_follow", line: "The easiest next step may be a short 20-minute review. We can go through the assessment together and identify the highest-value area to improve. Would Tuesday afternoon or Thursday morning work better?", isQuestion: true, expectedResponse: "Day/time"},
      ],
    },
  },
  firstDiscoveryQuestions: [
    "Great. To make this relevant, could you walk me through one repetitive or manual process that takes too much time for your team today?",
    "What administrative task takes the most time each week?",
    "Where does your team still rely heavily on spreadsheets, email, or paper?",
    "Which process creates the most delay, duplicate entry, or follow-up work?",
    "What is one workflow you would improve first if you had the chance?",
  ],
  meetingClose: {
    wording: "The easiest next step may be a short 20-minute review. We can go through the assessment together and identify the highest-value area to improve. Would Tuesday afternoon or Thursday morning work better?",
    alternatives: [
      "Could we schedule a brief call to review the results together?",
      "Would next week work for a short discovery call?",
    ],
  },
  assessmentClose: {
    wording: "Perfect. I can send you the assessment link now. It takes about eight to ten minutes, and once you complete it, you'll receive a summary of your biggest automation opportunities.",
    alternatives: [
      "Would you prefer to complete it on your own, or review together?",
    ],
  },
};

type ScriptMode = "script" | "dynamic" | "transitioning";

export function CopilotPanel({ callId, isCallActive, segments, contacts }: Props) {
  const [connected, setConnected] = useState(false);
  const [gps, setGPS] = useState<GPSData | null>(null);
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [health, setHealth] = useState<DealHealth | null>(null);
  const [fastState, setFastState] = useState<FastCoachState | null>(null);
  const [status, setStatus] = useState<CoachStatus>("connecting");
  const [aiRefining, setAiRefining] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [usedKeys, setUsedKeys] = useState<Set<string>>(new Set());
  const [dismissedKeys, setDismissedKeys] = useState<Set<string>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);
  const sentRef = useRef<Set<string>>(new Set());
  const seenKeys = useRef<Set<string>>(new Set());
  const statusTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const refineTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Opening Script state ──
  const [scriptMode, setScriptMode] = useState<ScriptMode>("script");
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [activeBranch, setActiveBranch] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [showScriptCollapsed, setShowScriptCollapsed] = useState(false);

  // Resolve contact name
  const contactFirstName = contacts?.[0]?.firstName || null;
  const resolvedName = contactFirstName || "{name}";

  // Get active script steps
  const openingScript = DEFAULT_OPENING_SCRIPT;
  const activeSteps = activeBranch && openingScript.branches[activeBranch]
    ? openingScript.branches[activeBranch].nextSteps
    : openingScript.steps;
  
  const currentStep = activeSteps[currentStepIdx] || null;
  const isLastStep = currentStepIdx >= activeSteps.length - 1;

  // ── Auto-detect branch from transcript ──
  useEffect(() => {
    if (scriptMode !== "script" || activeBranch) return;
    const segs = segments || [];
    const lastProspectText = segs.filter(s => s.sourceRole === "prospect" || s.speaker !== "PNS Agent")
      .map(s => s.text).join(" ").toLowerCase();
    if (!lastProspectText || lastProspectText.length < 3) return;

    for (const [branchId, branch] of Object.entries(openingScript.branches)) {
      if (branch.matchKeywords.some(kw => lastProspectText.includes(kw))) {
        setActiveBranch(branchId);
        setCurrentStepIdx(0);
        return;
      }
    }
  }, [segments, scriptMode, activeBranch]);

  // ── Auto-mark steps complete from transcript ──
  useEffect(() => {
    if (scriptMode !== "script" || !currentStep) return;
    const segs = segments || [];
    const allAgentText = segs.filter(s => s.sourceRole === "agent" || s.speaker === "PNS Agent")
      .map(s => s.text.toLowerCase()).join(" ");
    
    // Simple keyword matching: if the agent's spoken text contains key words from this step
    const lineWords = currentStep.line.toLowerCase().replace("{name}", resolvedName.toLowerCase()).split(" ").filter(w => w.length > 3);
    const matchCount = lineWords.filter(w => allAgentText.includes(w)).length;
    if (matchCount >= Math.min(3, lineWords.length * 0.5) && allAgentText.length > 10) {
      setCompletedSteps(prev => new Set([...prev, currentStep.id]));
    }
  }, [segments, scriptMode, currentStep, resolvedName]);

  // ── Transition: detect substantive prospect answer → switch to dynamic ──
  useEffect(() => {
    if (scriptMode !== "script") return;
    const segs = segments || [];
    const prospectFinals = segs.filter(s => s.isFinal && (s.sourceRole === "prospect" || s.speaker !== "PNS Agent"));
    if (prospectFinals.length >= 3) {
      // Prospect has said enough — transition
      setScriptMode("dynamic");
      setShowScriptCollapsed(true);
    }
    // Pain point detection
    const painWords = ["problem", "challenge", "issue", "manual", "paper", "spreadsheet", "excel", "time", "cost", "reporting"];
    const allProspectText = prospectFinals.map(s => s.text.toLowerCase()).join(" ");
    if (painWords.some(w => allProspectText.includes(w)) && prospectFinals.length >= 1) {
      setScriptMode("dynamic");
      setShowScriptCollapsed(true);
    }
  }, [segments, scriptMode]);

  // Script navigation
  const nextStep = () => {
    if (isLastStep) return;
    setCompletedSteps(prev => currentStep ? new Set([...prev, currentStep.id]) : prev);
    setCurrentStepIdx(i => i + 1);
  };
  const prevStep = () => setCurrentStepIdx(i => Math.max(0, i - 1));
  const markSaid = () => {
    if (currentStep) setCompletedSteps(prev => new Set([...prev, currentStep.id]));
    if (!isLastStep) setCurrentStepIdx(i => i + 1);
  };
  const switchToDynamic = () => {
    setScriptMode("dynamic");
    setShowScriptCollapsed(true);
  };
  const restartScript = () => {
    setCurrentStepIdx(0);
    setActiveBranch(null);
    setCompletedSteps(new Set());
    setScriptMode("script");
    setShowScriptCollapsed(false);
  };

  // Resolve line text
  const resolveLine = (line: string) => line.replace("{name}", resolvedName);

  // ── Auto-advance status when we have segments ──
  const lastSegCount = useRef(0);
  useEffect(() => {
    const segs = segments || [];
    if (segs.length > lastSegCount.current) {
      lastSegCount.current = segs.length;
      // Cycle through informative statuses
      const statusCycle: CoachStatus[] = [
        "listening", "identifying_question", "updating_discovery",
        "checking_objections", "preparing_recommendation",
      ];
      const idx = segs.length % statusCycle.length;
      if (status !== "ai_refining" && status !== "connecting") {
        setStatus(statusCycle[idx]);
      }
      // Return to "listening" after brief display
      if (statusTimer.current) clearTimeout(statusTimer.current);
      statusTimer.current = setTimeout(() => {
        setStatus("listening");
      }, 2000);
    }
    return () => {
      if (statusTimer.current) clearTimeout(statusTimer.current);
    };
  }, [segments?.length]);

  useEffect(() => {
    if (!callId || !isCallActive) return;
    setStatus("connecting");
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/^https?:\/\//, "");
    const ws = new WebSocket(`${proto}//${host}/api/v1/sales-coach/coach/ws/${callId}`);
    wsRef.current = ws;
    ws.onopen = () => { setConnected(true); setStatus("listening"); };
    ws.onclose = () => { setConnected(false); setStatus("connecting"); };
    ws.onerror = () => { setConnected(false); setStatus("connecting"); };
    ws.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        
        // GPS data
        if (d.metadata?.gps) setGPS(d.metadata.gps as GPSData);
        if (d.gps) setGPS(d.gps as GPSData);
        
        // Deal health
        if (d.metadata?.deal_health) setHealth(d.metadata.deal_health as DealHealth);
        
        // Fast coach state (includes grace period info)
        if (d.fast_coach) setFastState(d.fast_coach as FastCoachState);
        
        // Recommendation — single card replacement via semantic key
        if (d.event_type === "ai_whisper" || d.type === "ai_whisper" ||
            d.type === "coach_event" && d.event_type === "ai_whisper") {
          const newRec: Recommendation = {
            priority: d.metadata?.priority || d.severity,
            key: d.metadata?.key || d.title,
            title: d.title,
            detail: d.description,
            suggested_wording: d.suggestion || d.metadata?.suggested_wording,
            reason: d.description,
            evidence: d.evidence || d.metadata?.evidence,
            expected_outcome: d.metadata?.expected_outcome,
            alternatives: d.metadata?.alternatives || [],
            transition: d.metadata?.transition,
            expires_when: d.metadata?.expires_when,
            action: d.suggestion,
            confidence: d.confidence,
            source: d.metadata?.source || "ai",
            partial: d.metadata?.partial || false,
            category: d.metadata?.category,
            stage: d.metadata?.stage,
            based_on_segment: d.metadata?.based_on_segment,
            relevance_version: d.metadata?.relevance_version,
            created_at: d.metadata?.created_at,
          };
          
          // Dedup by semantic key — only show new unique recommendations
          const recKey = newRec.key || newRec.title || "";
          if (!seenKeys.current.has(recKey) || newRec.source === "ai") {
            // Fast coach replaces fast; AI always replaces
            if (newRec.source === "ai" || !seenKeys.current.has(recKey)) {
              seenKeys.current.add(recKey);
              if (seenKeys.current.size > 30) {
                const arr = [...seenKeys.current];
                seenKeys.current = new Set(arr.slice(-20));
              }
            }
            setRec(newRec);
            
            if (newRec.partial) {
              setAiRefining(true);
              setStatus("ai_refining");
            } else {
              setAiRefining(false);
              if (refineTimer.current) { clearTimeout(refineTimer.current); refineTimer.current = null; }
              setStatus(newRec.source === "ai" ? "ready" : "listening");
            }
          }
        }
        
        // Conversation state update
        if (d.type === "conversation_state") {
          if (d.gps) setGPS(d.gps as GPSData);
          if (d.recommendation) setRec(d.recommendation as Recommendation);
          if (d.fast_coach) setFastState(d.fast_coach as FastCoachState);
        }
      } catch { /* ignore */ }
    };
    return () => { 
      ws.close(); 
      wsRef.current = null; 
      if (refineTimer.current) { clearTimeout(refineTimer.current); refineTimer.current = null; }
    };
  }, [callId, isCallActive]);

  // ── Forward segments to coach WebSocket ──
  useEffect(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const segs = segments || [];
    for (const seg of segs) {
      if (!sentRef.current.has(seg.id) && seg.isFinal) {
        sentRef.current.add(seg.id);
        wsRef.current.send(JSON.stringify({
          type: "segment", speaker: seg.speaker, text: seg.text,
          start: seg.start, end: seg.end, is_final: true,
          confidence: seg.confidence,
          source_role: seg.sourceRole || (seg.speaker === "PNS Agent" ? "agent" : "prospect"),
        }));
        setStatus("preparing_recommendation");
        // ── Timeout: if no response in 4s, go back to listening ──
        if (refineTimer.current) clearTimeout(refineTimer.current);
        refineTimer.current = setTimeout(() => {
          setAiRefining(false);
          setStatus("listening");
        }, 4000);
      }
    }
  }, [segments]);

  // ── Grace period for speaking ratio ──
  const inGracePeriod = fastState?.grace_period_active ?? true;
  const talkRatioPct = fastState ? Math.round((fastState.talk_ratio ?? 0.5) * 100) : 50;

  if (!callId || !isCallActive) return null;

  const StatusIcon = STATUS_LABELS[status];
  
  // Shared segment array
  const segs = segments || [];
  
  // ── Stale recommendation detection ──
  const recBasedOnSegment = rec && (rec as Record<string, unknown>).based_on_segment as number | undefined;
  const currentSegmentCount = fastState?.segments_processed ?? segs.filter(s => s.isFinal).length;
  const isStale = recBasedOnSegment != null && currentSegmentCount > recBasedOnSegment + 3;

  return (
    <div className="flex flex-col h-full bg-gray-900/95 border border-gray-700/50 rounded-2xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700/50 bg-gray-900">
        <div className="flex items-center gap-2">
          <Brain className={`w-5 h-5 ${connected ? "text-purple-400 animate-pulse" : "text-gray-500"}`} />
          <span className="text-sm font-semibold text-gray-200">Copilot</span>
          {aiRefining && <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />}
          {fastState?.segments_processed != null && (
            <span className="text-[11px] text-gray-600">{fastState.segments_processed} segs</span>
          )}
        </div>
        <span className="text-[11px] text-gray-500">{gps?.completed_count ?? 0}/{gps?.total_count ?? 9}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {/* ── STATUS BAR — never blank ── */}
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-gray-800/40 border border-gray-700/30">
          {StatusIcon.icon}
          <span className="text-xs text-gray-400">
            {scriptMode === "script" ? "Opening Mode" : StatusIcon.label}
          </span>
          {inGracePeriod && fastState?.both_channels_live === false && (
            <span className="text-[11px] text-gray-600 ml-auto">warming up</span>
          )}
        </div>

        {/* ── FULL-SCRIPT OPENING MODE — teleprompter layout ── */}
        {scriptMode === "script" && (
          <div className="p-2.5 rounded-lg bg-emerald-400/5 border border-emerald-400/20">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Play className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Opening Script</span>
              </div>
              <button onClick={switchToDynamic} className="text-[11px] text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1">
                <SkipForward className="w-3 h-3" />Skip to AI
              </button>
            </div>

            {/* Full script — all lines visible, current highlighted */}
            <div className="space-y-0.5 mb-2 max-h-[340px] overflow-y-auto">
              {activeSteps.map((step, idx) => {
                const isCompleted = completedSteps.has(step.id);
                const isCurrent = idx === currentStepIdx;
                const isPast = idx < currentStepIdx;
                
                return (
                  <div key={step.id} className={`px-2 py-1 rounded transition-all ${
                    isCurrent ? "bg-emerald-400/10 border border-emerald-400/30" :
                    isPast ? "opacity-40" :
                    "opacity-60"
                  }`}>
                  <p className={`text-sm leading-relaxed ${
                      isCurrent ? "text-emerald-300 font-medium" :
                      isPast ? "text-gray-500 line-through" :
                      "text-gray-400"
                    }`}>
                      {isCompleted && <Check className="w-2.5 h-2.5 text-emerald-400 inline mr-1" />}
                      &ldquo;{resolveLine(step.line)}&rdquo;
                    </p>
                    {step.isQuestion && isCurrent && step.expectedResponse && (
                      <p className="text-[10px] text-gray-500 mt-0.5 ml-4 italic">
                        Expected: {step.expectedResponse}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Response branches — only show when on a question step */}
            {currentStep?.isQuestion && !activeBranch && (
              <div className="mb-2 p-2 rounded bg-gray-800/40 border border-gray-700/30">
                <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">Response</p>
                <div className="grid grid-cols-3 gap-1">
                  {Object.entries(openingScript.branches).filter(([id]) => 
                    ["yes", "no", "partially", "busy", "not_interested", "what_is_pns"].includes(id)
                  ).map(([id, branch]) => (
                    <button
                      key={id}
                      onClick={() => { setActiveBranch(id); setCurrentStepIdx(0); }}
                      className={`text-[11px] px-2 py-1 rounded font-medium transition-colors ${
                        id === "yes" ? "bg-emerald-400/20 text-emerald-400 hover:bg-emerald-400/30" :
                        id === "no" ? "bg-amber-400/20 text-amber-400 hover:bg-amber-400/30" :
                        id === "busy" ? "bg-red-400/20 text-red-400 hover:bg-red-400/30" :
                        "bg-gray-700/50 text-gray-400 hover:bg-gray-600/50"
                      }`}
                    >
                      {branch.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Active branch indicator + branch script */}
            {activeBranch && (
              <div className="mb-2 p-2 rounded bg-cyan-400/5 border border-cyan-400/20">
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[11px] text-cyan-400 font-medium">
                    {openingScript.branches[activeBranch]?.label || activeBranch}
                  </p>
                  <button onClick={() => { setActiveBranch(null); setCurrentStepIdx(0); }} className="text-[10px] text-gray-500 hover:text-gray-300">
                    Back
                  </button>
                </div>
                {/* Branch full script — same teleprompter style */}
                <div className="space-y-0.5 mb-1.5">
                  {activeSteps.map((step, idx) => {
                    const isCurr = idx === currentStepIdx;
                    const isPast = idx < currentStepIdx;
                    return (
                      <div key={step.id} className={`px-2 py-0.5 rounded ${isCurr ? "bg-cyan-400/10 border border-cyan-400/20" : isPast ? "opacity-40" : "opacity-60"}`}>
                        <p className={`text-xs leading-relaxed ${isCurr ? "text-cyan-300 font-medium" : isPast ? "text-gray-500 line-through" : "text-gray-400"}`}>
                          {completedSteps.has(step.id) && <Check className="w-2 h-2 text-emerald-400 inline mr-1" />}
                          &ldquo;{resolveLine(step.line)}&rdquo;
                        </p>
                      </div>
                    );
                  })}
                </div>
                {/* If this branch leads to another question, show sub-branches */}
                {currentStep?.isQuestion && ["assessment_yes", "send_link", "yes_ask"].includes(currentStep.id) && (
                  <div className="mt-1.5 pt-1.5 border-t border-gray-700/30">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Next Response</p>
                    <div className="flex flex-wrap gap-1">
                      {activeBranch === "yes" && currentStep.id === "yes_ask" && (
                        <>
                          <button onClick={() => { setActiveBranch("assessment_yes"); setCurrentStepIdx(0); }} className="text-[9px] px-2 py-1 rounded bg-emerald-400/20 text-emerald-400 hover:bg-emerald-400/30 font-medium">
                            Yes — take it
                          </button>
                          <button onClick={() => { setActiveBranch("send_link"); setCurrentStepIdx(0); }} className="text-[9px] px-2 py-1 rounded bg-cyan-400/20 text-cyan-400 hover:bg-cyan-400/30">
                            Send link
                          </button>
                          <button onClick={() => { setActiveBranch("busy"); setCurrentStepIdx(0); }} className="text-[9px] px-2 py-1 rounded bg-amber-400/20 text-amber-400 hover:bg-amber-400/30">
                            Busy now
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Assessment-conversion guidance — shown after qualification */}
            {activeBranch === "assessment_yes" && currentStep?.id === "as_mode" && (
              <div className="mb-2 p-2 rounded bg-purple-400/5 border border-purple-400/20">
                <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-1 font-semibold">Conversion Options</p>
                <div className="space-y-1">
                  <div className="p-1.5 rounded bg-purple-400/5 border border-purple-400/10">
                    <p className="text-[11px] text-purple-300 font-medium">Send link now</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">I can send you the assessment link now. It takes about eight to ten minutes.</p>
                  </div>
                  <div className="p-1.5 rounded bg-purple-400/5 border border-purple-400/10">
                    <p className="text-[11px] text-purple-300 font-medium">Schedule review</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">Would you prefer to schedule a short call where we can review the results together?</p>
                  </div>
                  <div className="p-1.5 rounded bg-purple-400/5 border border-purple-400/10">
                    <p className="text-[11px] text-purple-300 font-medium">Meeting close</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">Would Tuesday afternoon or Thursday morning work better?</p>
                  </div>
                </div>
              </div>
            )}

            {/* Script controls */}
            <div className="flex items-center gap-1 pt-1.5 border-t border-gray-700/30">
              <button onClick={prevStep} disabled={currentStepIdx === 0} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400 hover:text-gray-300 disabled:opacity-30 transition-colors flex items-center gap-0.5">
                <ArrowLeft className="w-3 h-3" /> Prev
              </button>
              <button onClick={markSaid} className="text-[10px] px-2 py-0.5 rounded bg-emerald-400/10 text-emerald-400 hover:bg-emerald-400/20 transition-colors flex items-center gap-0.5">
                <Check className="w-3 h-3" /> Said
              </button>
              <button onClick={nextStep} disabled={isLastStep} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400 hover:text-gray-300 disabled:opacity-30 transition-colors flex items-center gap-0.5">
                Next <ArrowRight className="w-3 h-3" />
              </button>
              <button onClick={restartScript} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400 hover:text-gray-300 transition-colors ml-auto">
                Restart
              </button>
            </div>

            {/* Step indicator */}
            <div className="mt-1 flex items-center gap-1">
              {activeSteps.map((s, i) => (
                <div key={s.id} className={`h-0.5 flex-1 rounded-full transition-colors ${
                  i < currentStepIdx ? "bg-emerald-500" :
                  i === currentStepIdx ? "bg-emerald-400 animate-pulse" :
                  "bg-gray-700"
                }`} />
              ))}
              <span className="text-[10px] text-gray-600 ml-1">{currentStepIdx + 1}/{activeSteps.length}</span>
            </div>
          </div>
        )}

        {/* ── AI INIT STATUS — shown during opening ── */}
        {scriptMode === "script" && (
          <div className="p-1.5 rounded-md bg-gray-800/30 border border-gray-700/20">
            <div className="flex items-center gap-1.5">
              {connected ? (
                <Activity className="w-2.5 h-2.5 text-cyan-400 animate-pulse" />
              ) : (
                <Loader2 className="w-2.5 h-2.5 text-gray-500 animate-spin" />
              )}
              <span className="text-[10px] text-gray-500">
                {connected ? "AI coaching ready in background" : "Preparing live coaching…"}
              </span>
            </div>
          </div>
        )}

        {/* ── Collapsed script reference when in dynamic mode ── */}
        {scriptMode === "dynamic" && showScriptCollapsed && (
          <div className="p-2 rounded-lg bg-gray-800/30 border border-gray-700/30">
            <button 
              onClick={() => setShowScriptCollapsed(false)}
              className="flex items-center justify-between w-full text-left"
            >
              <div className="flex items-center gap-1.5">
                <Play className="w-4 h-4 text-gray-500" />
                <span className="text-[11px] text-gray-500">Opening Script</span>
                <span className="text-[10px] text-gray-600">
                  Step {currentStepIdx + 1}/{activeSteps.length}
                  {activeBranch && ` · ${openingScript.branches[activeBranch]?.label}`}
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-600" />
            </button>
            <div className="mt-1.5 pt-1.5 border-t border-gray-700/30">
              <div className="flex gap-1">
                <button onClick={restartScript} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400 hover:text-gray-300 transition-colors">
                  Reopen
                </button>
                <button onClick={() => setShowScriptCollapsed(false)} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400 hover:text-gray-300 transition-colors">
                  Hide
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Speaking Ratio (only after grace period) ── */}
        {!inGracePeriod && (
          <div className="p-2 rounded-lg bg-gray-800/30 border border-gray-700/30">
            <div className="flex items-center gap-1.5 mb-1">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-xs text-gray-400">Speaking Ratio</span>
              <span className="text-[11px] text-gray-600 ml-auto">{talkRatioPct}% you</span>
            </div>
            <div className="h-1.5 rounded-full bg-gray-700 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  talkRatioPct > 70 ? "bg-red-500" : talkRatioPct < 25 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${talkRatioPct}%` }}
              />
            </div>
            {talkRatioPct > 70 && (
              <p className="text-[9px] text-red-400 mt-1">You&apos;re speaking too much — ask an open question</p>
            )}
          </div>
        )}

        {/* GPS Widget */}
        {gps && (
          <div className="p-2.5 rounded-lg bg-gray-800/50 border border-gray-700/50">
            <div className="flex items-center gap-1.5 mb-2">
              <Navigation className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">GPS</span>
            </div>
            <div className="h-1 rounded-full bg-gray-700 mb-2">
              <div className="h-1 rounded-full bg-cyan-500 transition-all" style={{ width: `${gps.progress_pct || 0}%` }} />
            </div>
            <p className="text-sm text-gray-300 mb-1.5">
              <span className="text-gray-500">→ </span>
              <span className="font-medium">{gps.current_destination || "Build Rapport"}</span>
            </p>
            <div className="flex flex-wrap gap-1">
              {gps.stages?.slice(0, 8).map(s => (
                <span key={s.key} className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                  s.status === "completed" ? "bg-emerald-400/20 text-emerald-400" :
                  s.status === "current" ? "bg-cyan-400/20 text-cyan-400 animate-pulse" :
                  "bg-gray-700 text-gray-500"
                }`}>{s.label.substring(0, 10)}</span>
              ))}
            </div>
          </div>
        )}

        {/* ONE Recommendation — card replacement, never append */}
        {rec && !dismissedKeys.has(rec.key || "") && !usedKeys.has(rec.key || "") && (
          <div className={`p-2.5 rounded-lg border transition-all duration-300 ${
            rec.partial ? "opacity-80" : ""
          } ${isStale ? "opacity-60" : ""} ${
            rec.priority === "critical" ? "bg-red-400/10 border-red-400/30" :
            rec.priority === "high" ? "bg-amber-400/10 border-amber-400/30" :
            "bg-purple-400/10 border-purple-400/20"
          }`}>
            <div className="flex items-center gap-1.5 mb-1">
              <Zap className={`w-3 h-3 flex-shrink-0 ${
                rec.priority === "critical" ? "text-red-400" :
                rec.priority === "high" ? "text-amber-400" : "text-purple-400"
              }`} />
              <span className="text-xs font-semibold text-gray-200 leading-tight flex-1">{rec.title}</span>
              {rec.source === "fast" && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-400/20 text-cyan-400 flex-shrink-0">FAST</span>
              )}
              {rec.source === "ai" && !rec.partial && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-400/20 text-purple-400 flex-shrink-0">AI</span>
              )}
              {rec.partial && (
                <Loader2 className="w-3.5 h-3.5 text-purple-400 animate-spin flex-shrink-0" />
              )}
            </div>

            {/* Suggested wording — the main actionable content */}
            {rec.suggested_wording && (
              <div className="mt-1.5 p-2 rounded bg-gray-800/60 border border-gray-700/40">
                <p className="text-sm text-purple-300 italic leading-relaxed">
                  &ldquo;{rec.suggested_wording}&rdquo;
                </p>
              </div>
            )}

            {/* Fallback: action */}
            {!rec.suggested_wording && rec.action && (
              <p className="text-sm text-purple-400 mt-1 italic leading-snug">{rec.action}</p>
            )}

            {/* Reason / evidence */}
            {rec.reason && (
              <p className="text-xs text-gray-400 mt-1.5 leading-snug">
                {rec.reason}
              </p>
            )}

            {/* Evidence */}
            {rec.evidence && rec.evidence !== "Call opening" && rec.evidence !== "Call start" && (
              <p className="text-[11px] text-gray-500 mt-1 italic">
                Triggered by: &ldquo;{rec.evidence.length > 100 ? rec.evidence.slice(0, 100) + "…" : rec.evidence}&rdquo;
              </p>
            )}

            {/* Alternatives — expandable */}
            {rec.alternatives && rec.alternatives.length > 0 && (
              <div className="mt-1.5">
                <button
                  onClick={() => setShowAlternatives(!showAlternatives)}
                  className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showAlternatives ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  {showAlternatives ? "Hide" : "Show"} {rec.alternatives.length} alternative{rec.alternatives.length > 1 ? "s" : ""}
                </button>
                {showAlternatives && (
                  <div className="mt-1 space-y-0.5">
                    {rec.alternatives.map((alt, i) => (
                      <p key={i} className="text-[11px] text-gray-500 pl-4 border-l border-gray-700">
                        {alt}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Expected outcome */}
            {rec.expected_outcome && (
              <p className="text-[11px] text-emerald-400/70 mt-1">
                → {rec.expected_outcome}
              </p>
            )}

            {/* Transition */}
            {rec.transition && (
              <p className="text-[11px] text-cyan-400/60 mt-0.5 italic">
                Transition: &ldquo;{rec.transition}&rdquo;
              </p>
            )}

            {/* User interaction buttons */}
            <div className="flex items-center gap-1 mt-2 pt-1.5 border-t border-gray-700/30">
              <button
                onClick={() => {
                  setUsedKeys(prev => new Set([...prev, rec.key || ""]));
                  // Optionally notify backend
                }}
                className="flex items-center gap-0.5 text-[10px] px-2 py-0.5 rounded bg-emerald-400/10 text-emerald-400 hover:bg-emerald-400/20 transition-colors"
                title="Mark as used"
              >
                <Check className="w-3 h-3" />
                Used
              </button>
              <button
                onClick={() => setDismissedKeys(prev => new Set([...prev, rec.key || ""]))}
                className="flex items-center gap-0.5 text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-500 hover:text-gray-300 transition-colors"
                title="Dismiss"
              >
                <X className="w-3 h-3" />
                Dismiss
              </button>
              <button
                onClick={() => setShowAlternatives(!showAlternatives)}
                className="flex items-center gap-0.5 text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-500 hover:text-gray-300 transition-colors ml-auto"
                title="More options"
              >
                <RefreshCw className="w-3 h-3" />
                Alternatives
              </button>
            </div>

            {rec.confidence && (
              <div className="mt-1 flex items-center gap-1">
                <div className="flex-1 h-0.5 rounded-full bg-gray-700">
                  <div
                    className={`h-0.5 rounded-full ${
                      (rec.confidence || 0) > 80 ? "bg-emerald-500" :
                      (rec.confidence || 0) > 60 ? "bg-amber-500" : "bg-red-500"
                    }`}
                    style={{ width: `${rec.confidence}%` }}
                  />
                </div>
                <span className="text-[10px] text-gray-600">{rec.confidence}%</span>
              </div>
            )}
          </div>
        )}

        {/* Deal Health */}
        {health && (
          <div className="p-2 rounded-lg bg-gray-800/30 border border-gray-700/30">
            <div className="grid grid-cols-3 gap-1">
              {[
                { l: "Discovery", v: health.discovery_quality ?? 0, c: "text-cyan-400" },
                { l: "Intent", v: health.buying_intent ?? 0, c: "text-emerald-400" },
                { l: "Close", v: health.close_probability ?? 0, c: "text-purple-400" },
              ].map(m => (
                <div key={m.l} className="text-center">
                  <span className={`text-base font-bold ${m.c}`}>{m.v}%</span>
                  <p className="text-[10px] text-gray-500">{m.l}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
