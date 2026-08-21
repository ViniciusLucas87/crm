export type NeverMissTradeSolution = {
  slug: "hvac-contractors" | "plumbers" | "electricians";
  title: string;
  seoTitle: string;
  description: string;
  eyebrow: string;
  hero: string;
  problem: string;
  example: string;
  fitPoints: string[];
  setupPoints: string[];
  faq: { question: string; answer: string }[];
};

export const neverMissTradeSolutions: Record<string, NeverMissTradeSolution> = {
  "hvac-contractors": {
    slug: "hvac-contractors",
    title: "Missed-call follow-up for HVAC contractors",
    seoTitle: "Missed-Call Text Back for HVAC Contractors | Never Miss",
    description:
      "Never Miss helps HVAC teams acknowledge eligible unanswered callers and organize the callback without changing the business number customers already use.",
    eyebrow: "Never Miss for HVAC contractors",
    hero: "Keep urgent HVAC callers from going quiet while your team is on a job.",
    problem:
      "Heating and cooling calls can arrive while a technician is driving, diagnosing equipment, or helping another customer. When the office cannot answer, the caller still needs to know what happens next.",
    example:
      "A homeowner calls about a furnace or air-conditioning problem. If the call is eligible and goes unanswered, Never Miss can send the business's configured reply and place the caller on a callback list. Your team decides how to prioritize and respond once someone is free.",
    fitPoints: [
      "Your technicians cannot always answer while working safely on site.",
      "The office needs a clearer way to see unanswered calls and callbacks.",
      "You want customers to keep calling the number already on your trucks, website, and ads.",
    ],
    setupPoints: [
      "Choose the reply customers receive after an eligible unanswered call.",
      "Set unanswered-call forwarding only with your carrier. Do not use all-calls forwarding.",
      "Complete a real unanswered-call test before relying on the workflow.",
    ],
    faq: [
      {
        question: "Does Never Miss replace an HVAC dispatcher?",
        answer:
          "No. It is a narrow missed-call recovery workflow. Your team still answers calls, decides urgency, schedules work, and speaks with customers.",
      },
      {
        question: "Do we need a new business number?",
        answer:
          "No. Customers continue calling your existing business number. The workflow depends on carrier forwarding for unanswered calls only.",
      },
      {
        question: "How do we know the setup works?",
        answer:
          "After forwarding is configured, place a real unanswered test call and confirm the reply, customer response, callback task, and your team's notification end to end.",
      },
    ],
  },
  plumbers: {
    slug: "plumbers",
    title: "Missed-call follow-up for plumbing businesses",
    seoTitle: "Missed-Call Text Back for Plumbers | Never Miss",
    description:
      "Never Miss helps plumbing businesses acknowledge eligible unanswered calls and organize callbacks while the team is on site, driving, or helping another customer.",
    eyebrow: "Never Miss for plumbers",
    hero: "When you cannot answer the phone, give the caller a clear next step.",
    problem:
      "Plumbing calls often happen while the owner or crew is in a crawlspace, with a customer, or travelling between jobs. A call that reaches voicemail can be difficult to recover later, especially when the caller needs help now.",
    example:
      "A caller reaches your existing business number while your crew is busy. When the call is eligible and unanswered, Never Miss can send your configured message and keep the callback visible for your team. You can then return the call with the caller's number and context in one place.",
    fitPoints: [
      "Calls matter to estimates, repairs, and ongoing customer service.",
      "The person answering the phone may also be working in the field.",
      "You need a simple callback handoff instead of relying on memory or voicemail.",
    ],
    setupPoints: [
      "Write a plain-language reply that reflects your business and working hours.",
      "Forward unanswered calls only, leaving always-forward, busy, and unreachable settings off.",
      "Test the actual call, text, customer reply, and callback task with your carrier before going live.",
    ],
    faq: [
      {
        question: "Will every plumbing call be sent to Never Miss?",
        answer:
          "No. Your team receives the call first. The workflow is configured for eligible unanswered calls, so the carrier forwarding setting is an important part of setup.",
      },
      {
        question: "Can we choose what the reply says?",
        answer:
          "Yes. Your team reviews the reply during setup. Keep it specific, polite, and realistic about when someone will call back.",
      },
      {
        question: "What should we test before using it with customers?",
        answer:
          "Test from a real phone after carrier forwarding is active. Confirm that a missed call is detected, the recovery text arrives, a reply is received, and the callback is visible to your team.",
      },
    ],
  },
  electricians: {
    slug: "electricians",
    title: "Missed-call follow-up for electrical contractors",
    seoTitle: "Missed-Call Text Back for Electricians | Never Miss",
    description:
      "Never Miss helps electrical contractors acknowledge eligible unanswered callers and keep callbacks organized without changing the number customers already recognize.",
    eyebrow: "Never Miss for electricians",
    hero: "Protect the callback while your electricians stay focused on the work in front of them.",
    problem:
      "Electrical work demands attention. Whether the team is troubleshooting, working at a panel, or moving between projects, it is not always practical or safe to answer the phone. That does not mean the next caller should be left without a response.",
    example:
      "A homeowner or project contact calls your usual business number while your team is on site. If the call is eligible and unanswered, Never Miss can send the reply you approve and create a callback item. Your team remains responsible for confirming scope, urgency, and scheduling.",
    fitPoints: [
      "Your team often works where an interrupted call is not practical.",
      "Homeowners, property managers, and builders still need a prompt acknowledgement.",
      "You want one clear list of callbacks without replacing your current number.",
    ],
    setupPoints: [
      "Confirm the business number and the person who should receive callback notifications.",
      "Configure no-answer forwarding with the carrier instead of forwarding all calls.",
      "Run an end-to-end unanswered-call test and record that the workflow is working before customer use.",
    ],
    faq: [
      {
        question: "Does Never Miss answer electrical calls for us?",
        answer:
          "No. It is designed to acknowledge an eligible unanswered call by text and organize a callback. Your people handle the actual customer conversation and work decisions.",
      },
      {
        question: "Will callers see a different number?",
        answer:
          "Customers keep using the existing business number. Setup uses unanswered-call forwarding, which should be tested with your own carrier because forwarding behaviour can vary by plan.",
      },
      {
        question: "What happens if we cancel?",
        answer:
          "You can cancel before the trial ends to avoid the first monthly charge. When service ends, remove unanswered-call forwarding so callers return to your normal voicemail process.",
      },
    ],
  },
};

export const neverMissTradeSlugs = Object.keys(neverMissTradeSolutions);
