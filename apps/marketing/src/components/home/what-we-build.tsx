import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";
import {
  LayoutDashboard,
  Workflow,
  BarChart3,
  Bot,
  Plug,
  Wrench,
} from "lucide-react";

const buildCards = [
  {
    icon: LayoutDashboard,
    title: "Custom Business Applications",
    description:
      "Tailored web and mobile apps built for your unique workflows.",
  },
  {
    icon: Workflow,
    title: "Workflow Automation",
    description:
      "Automate repetitive tasks, approvals, and handoffs across your operation.",
  },
  {
    icon: BarChart3,
    title: "Dashboards & Reporting",
    description:
      "Current insights and KPIs that help you make faster decisions.",
  },
  {
    icon: Bot,
    title: "AI Document Tools",
    description:
      "Extract, summarize, and search documents with AI-powered tools.",
  },
  {
    icon: Plug,
    title: "Integrations",
    description:
      "Connect your systems, data, and tools so information flows cleanly.",
  },
  {
    icon: Wrench,
    title: "Ongoing Support & Maintenance",
    description:
      "Reliable support and maintenance to keep your systems running.",
  },
];

export function WhatWeBuild() {
  return (
    <Section variant="default" id="what-we-build">
      <Container>
        <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary">
          We build software and systems that solve real business problems,
          tailored to how your team actually works.
        </h2>
        <p className="mt-4 text-pns-text-muted max-w-2xl">
          Practical systems that streamline operations, reduce errors, and help
          your team get more done.
        </p>

        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {buildCards.map((card) => (
            <div
              key={card.title}
              className="p-6 rounded-[16px] bg-white border border-pns-text-primary/8 hover:border-pns-text-primary/15 transition-colors"
            >
              <card.icon
                className="w-8 h-8 text-pns-text-muted mb-4"
                aria-hidden="true"
              />
              <h3 className="font-bold text-pns-text-primary text-lg">
                {card.title}
              </h3>
              <p className="mt-2 text-sm text-pns-text-muted leading-relaxed">
                {card.description}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
