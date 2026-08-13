import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "Resources",
  description:
    "Practical tools, guides, research, and articles for Canadian businesses improving their operations and technology.",
};

const resources = [
  {
    title: "Free business tools",
    description:
      "Estimate manual-work costs, model automation ROI, and assess CRM readiness using transparent assumptions.",
    href: "/free-tools",
  },
  {
    title: "Business guides",
    description:
      "Straightforward answers to common questions about automation, CRM systems, custom software, and responsible AI use.",
    href: "/business-guides",
  },
  {
    title: "Research",
    description:
      "Carefully sourced planning benchmarks and methodology for Canadian small and midsize businesses.",
    href: "/research",
  },
  {
    title: "Articles",
    description:
      "Long-form perspectives on business processes, software decisions, and operational improvement.",
    href: "/blog",
  },
  {
    title: "Operations assessment",
    description:
      "A short guided review that identifies likely bottlenecks, time costs, and practical opportunities for improvement.",
    href: "/assessment",
  },
];

export default function ResourcesPage() {
  return (
    <>
      <section className="border-b border-black/8 bg-white py-20 lg:py-28">
        <Container>
          <div className="max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
              Resources
            </p>
            <h1 className="mt-5 text-[clamp(3rem,7vw,5.5rem)] font-semibold leading-[1.02] tracking-[-0.04em] text-pns-text-primary">
              Useful information for better operational decisions.
            </h1>
            <p className="mt-8 max-w-2xl text-xl leading-8 text-pns-text-muted">
              Tools and guidance for businesses evaluating automation, custom
              software, connected systems, and process improvement.
            </p>
          </div>
        </Container>
      </section>

      <section className="bg-pns-bg py-20 lg:py-28">
        <Container>
          <div className="border-t border-black/12">
            {resources.map((resource, index) => (
              <Link
                key={resource.title}
                href={resource.href}
                className="group grid gap-4 border-b border-black/12 py-8 sm:grid-cols-[56px_0.7fr_1.3fr_24px] sm:items-start"
              >
                <span className="text-sm text-pns-text-muted">0{index + 1}</span>
                <h2 className="text-xl font-semibold text-pns-text-primary">
                  {resource.title}
                </h2>
                <p className="leading-7 text-pns-text-muted">{resource.description}</p>
                <ArrowRight className="mt-1 h-5 w-5 text-pns-text-muted transition-transform group-hover:translate-x-1" />
              </Link>
            ))}
          </div>
        </Container>
      </section>
    </>
  );
}
