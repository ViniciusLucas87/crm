import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  ClipboardCheck,
  Clock,
  BarChart3,
  ArrowRight,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Free Business Tools for Canadian SMBs | Pacific North Systems",
  description:
    "Calculate manual work costs, automation ROI, and CRM readiness. Free, with no signup required. Built for Canadian small and midsize businesses by Pacific North Systems.",
  alternates: { canonical: "https://pacificnorthsystems.com/free-tools" },
  openGraph: {
    title: "Free Business Tools for Canadian SMBs",
    description:
      "Calculate manual work costs, automation ROI, and CRM readiness. Free, with no signup required.",
  },
};

interface ToolCard {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  metrics: string[];
  cta: string;
}

const tools: ToolCard[] = [
  {
    title: "Manual Work Cost Calculator",
    description:
      "See how much repetitive manual tasks are really costing your company each week and each year, and how many hours automation could give back.",
    href: "/free-tools/manual-work-cost-calculator",
    icon: Clock,
    metrics: ["Weekly cost", "Annual cost", "Hours recoverable"],
    cta: "Calculate your costs",
  },
  {
    title: "Automation ROI Calculator",
    description:
      "Get a clear, honest picture of what automation would return in the first year, including payback period, net benefit, and conservative estimates.",
    href: "/free-tools/automation-roi-calculator",
    icon: TrendingUp,
    metrics: ["Net first year benefit", "Payback months", "ROI percentage"],
    cta: "Estimate your ROI",
  },
  {
    title: "CRM Readiness Assessment",
    description:
      "Answer 10 practical questions about how your team manages leads and customers. Get a readiness score from 0 to 100 with prioritized next steps.",
    href: "/free-tools/crm-readiness-assessment",
    icon: ClipboardCheck,
    metrics: ["Readiness score", "Maturity band", "Action plan"],
    cta: "Check your readiness",
  },
];

export default function FreeToolsHub() {
  return (
    <>
      {/* Hero */}
      <Section variant="dark">
        <Container>
          <div className="flex flex-col items-center text-center max-w-3xl mx-auto py-8">
            <Badge>Free Tools</Badge>
            <h1 className="font-heading text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-white mt-4 mb-3">
              Free Business Tools for Canadian SMBs
            </h1>
            <p className="text-pns-text-light text-[15px] leading-relaxed max-w-xl">
              No signup. No credit card. Just honest, practical calculators and
              assessments built for Canadian businesses with complex operations.
            </p>
          </div>
        </Container>
      </Section>

      {/* Tool Cards */}
      <Section>
        <Container>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {tools.map((tool) => (
              <Card key={tool.href} className="flex flex-col h-full" variant="elevated">
                <div className="p-6 flex flex-col h-full">
                  <div className="w-10 h-10 rounded-[10px] bg-pns-soft-blue flex items-center justify-center mb-4">
                    <tool.icon className="w-5 h-5 text-[#051226]" />
                  </div>
                  <h3 className="font-heading font-semibold text-[18px] text-pns-text-primary mb-2">
                    {tool.title}
                  </h3>
                  <p className="text-pns-text-muted text-[15px] leading-relaxed mb-4 flex-1">
                    {tool.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {tool.metrics.map((m) => (
                      <span
                        key={m}
                        className="text-[13px] bg-pns-soft-blue text-pns-text-primary px-2.5 py-1 rounded-full"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                  <Link href={tool.href}>
                    <Button className="w-full">
                      {tool.cta}
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        </Container>
      </Section>

      {/* Why free? */}
      <Section variant="soft">
        <Container>
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="font-heading text-[clamp(1.5rem,3vw,2rem)] font-bold text-pns-text-primary mb-4">
              Why are these free?
            </h2>
            <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
              We believe that before you can decide whether automation or custom
              software is right for your business, you need honest numbers, not
              a sales pitch. These tools help you build a business case
              independently. If the numbers make sense for you, we&apos;re here
              to talk. If they don&apos;t, we&apos;ve still helped.
            </p>
            <Link href="/business-guides">
              <Button variant="outline">
                <BarChart3 className="w-4 h-4 mr-2" />
                Browse our Business Guides
              </Button>
            </Link>
          </div>
        </Container>
      </Section>

      {/* Guide CTA */}
      <Section>
        <Container>
          <div className="max-w-3xl mx-auto text-center">
            <Badge>Guides</Badge>
            <h2 className="font-heading text-[clamp(1.5rem,3vw,2rem)] font-bold text-pns-text-primary mt-3 mb-3">
              Practical Answers for Canadian Businesses
            </h2>
            <p className="text-pns-text-muted text-[15px] leading-relaxed mb-6">
              Straightforward articles covering automation, CRM, AI, and
              operations, written for Canadian SMB owners and operators.
            </p>
            <Link href="/business-guides">
              <Button>
                View all guides
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </Container>
      </Section>
    </>
  );
}
