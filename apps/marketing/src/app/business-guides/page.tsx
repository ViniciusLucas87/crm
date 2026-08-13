import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, BookOpen } from "lucide-react";

export const metadata: Metadata = {
  title: "Business Guides for Canadian SMBs | Pacific North Systems",
  description:
    "Practical guides in plain English on automation, CRM, AI, and operations for Canadian small and midsize business owners. No jargon and no sales pitch.",
  alternates: { canonical: "https://pacificnorthsystems.com/business-guides" },
};

interface Guide {
  title: string;
  slug: string;
  description: string;
  readTime: string;
  category: string;
}

const guides: Guide[] = [
  {
    title: "What Should I Automate First in My Business?",
    slug: "what-should-i-automate-first",
    description:
      "A practical framework for identifying which business process to automate first, based on volume, error rate, and employee impact, with real Canadian SMB examples.",
    readTime: "6 min",
    category: "Automation",
  },
  {
    title: "How Much Is Manual Paperwork Costing My Company?",
    slug: "manual-paperwork-cost",
    description:
      "Learn how to estimate the true loaded cost of manual data entry, paper workflows, and rekeying, and when automation pays for itself.",
    readTime: "5 min",
    category: "Operations",
  },
  {
    title: "Can AI Help My Business Without Replacing Employees?",
    slug: "ai-without-replacing-employees",
    description:
      "How Canadian SMBs are using AI for document processing, data extraction, and workflow assistance to support their teams rather than replace them.",
    readTime: "7 min",
    category: "AI",
  },
  {
    title: "How Do I Stop Leads from Falling Through the Cracks?",
    slug: "stop-leads-falling-through-cracks",
    description:
      "Five practical steps to ensure every lead gets a timely response, clear ownership, and consistent follow up, even when your team is busy.",
    readTime: "6 min",
    category: "Sales",
  },
  {
    title: "Do I Need a CRM for My Small Business?",
    slug: "do-i-need-a-crm",
    description:
      "When a shared inbox or spreadsheet stops working and a CRM becomes worth the investment. A decision guide for Canadian SMB owners.",
    readTime: "5 min",
    category: "CRM",
  },
  {
    title: "How Can I Connect Accounting, Email, Quoting, and Scheduling?",
    slug: "connect-accounting-email-quoting-scheduling",
    description:
      "A practical guide to integrating the four most common SMB tools: accounting software, email, quoting, and scheduling. The goal is to eliminate duplicate data entry.",
    readTime: "7 min",
    category: "Integrations",
  },
  {
    title: "Should I Build Custom Software or Buy Another Subscription?",
    slug: "build-vs-buy-software",
    description:
      "A cost-comparison framework for Canadian SMBs deciding between another SaaS subscription and custom-built software tailored to their workflow.",
    readTime: "8 min",
    category: "Strategy",
  },
  {
    title: "How Can I Use AI Securely with Customer Information?",
    slug: "ai-secure-customer-information",
    description:
      "Practical privacy and security considerations for Canadian businesses using AI tools with customer data, including PIPEDA basics, data isolation, and safe defaults.",
    readTime: "7 min",
    category: "AI",
  },
  {
    title: "How Many Hours Could Automation Save My Company?",
    slug: "automation-hours-saved",
    description:
      "A practical method to audit your team's repetitive tasks and estimate realistic automation time savings, with a link to our free calculator.",
    readTime: "6 min",
    category: "Automation",
  },
  {
    title: "Why Are Employees Entering the Same Information Multiple Times?",
    slug: "employees-entering-same-information",
    description:
      "The root causes of duplicate data entry in Canadian SMBs, including disconnected tools, manual handoffs, and paper workflows, and how to fix them systematically.",
    readTime: "5 min",
    category: "Operations",
  },
];

export default function BusinessGuidesHub() {
  return (
    <>
      <Section variant="dark">
        <Container>
          <div className="flex flex-col items-center text-center max-w-3xl mx-auto py-8">
            <Badge>Guides</Badge>
            <h1 className="font-heading text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-white mt-4 mb-3">
              Business Guides for Canadian SMBs
            </h1>
            <p className="text-pns-text-light text-[15px] leading-relaxed max-w-xl">
              Practical, plain-English answers to the questions Canadian business
              owners ask most about automation, CRM, AI, and operations.
            </p>
          </div>
        </Container>
      </Section>

      <Section>
        <Container>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {guides.map((guide) => (
              <Link key={guide.slug} href={`/business-guides/${guide.slug}`}>
                <Card className="h-full hover:shadow-md transition-shadow" variant="elevated">
                  <div className="p-6">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-[12px] font-medium bg-pns-soft-blue text-pns-text-primary px-2 py-0.5 rounded-full">
                        {guide.category}
                      </span>
                      <span className="text-[12px] text-pns-text-muted">
                        {guide.readTime} read
                      </span>
                    </div>
                    <h3 className="font-heading font-semibold text-[16px] text-pns-text-primary mb-2">
                      {guide.title}
                    </h3>
                    <p className="text-[14px] text-pns-text-muted leading-relaxed mb-3">
                      {guide.description}
                    </p>
                    <span className="text-[14px] font-medium text-pns-text-primary inline-flex items-center gap-1">
                      Read guide <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-pns-text-muted text-[15px] mb-4">
              These guides are written for Canadian SMB owners and operators.
              They include honest limitations, practical examples, and links
              to our free tools where relevant.
            </p>
            <Link href="/free-tools" className="text-[15px] font-medium text-pns-text-primary inline-flex items-center gap-1 hover:underline">
              <BookOpen className="w-4 h-4" />
              Try our free business calculators
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </Container>
      </Section>
    </>
  );
}
