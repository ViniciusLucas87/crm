import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Badge } from "@/components/ui/badge";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Editorial Methodology & Standards | Pacific North Systems",
  description:
    "How we research, write, and maintain content on pacificnorthsystems.com. Sourcing hierarchy, corrections policy, calculator methodology, AI-assistance disclosure, and author credentials.",
  alternates: { canonical: "https://www.pacificnorthsystems.com/methodology" },
};

const sections = [
  {
    heading: "Editorial Independence",
    body: "All content on pacificnorthsystems.com is created by Pacific North Systems for the benefit of Canadian small and midsize business owners and operators. We do not accept payment for editorial content, product placements, or sponsored posts. Our research, guides, and tools are produced independently and reflect our honest assessment of the available evidence. When we link to our own services, we disclose the relationship.",
  },
  {
    heading: "Sourcing Hierarchy",
    body: "We prefer primary Canadian government tables, releases, legislation, and regulator guidance. We may use peer-reviewed or association research when its publisher, date, scope, and method are disclosed. Practitioner observations are labelled as observations, and hypothetical calculator scenarios are never presented as measured customer results. We do not use AI output as evidence.",
  },
  {
    heading: "Corrections Policy",
    body: "If you find a factual error, contact hello@pacificnorthsystems.com with the subject line 'Correction' and include the source. We aim to review every request promptly. Confirmed substantive errors receive a visible correction note and date; minor clarity changes are included in the page version history.",
  },
  {
    heading: "Calculator Methodology",
    body: "Our free tools calculate in the browser. Inputs remain in the browser session unless a visitor deliberately submits the optional follow up form. Defaults are editable planning assumptions, not market averages. Each tool publishes its formula, a clearly hypothetical example, limitations, review date, and links to privacy information. Results are directional planning scenarios, not financial advice, validated diagnostics, or predictions.",
  },
  {
    heading: "AI-Assistance Disclosure",
    body: "Some content on this site may be drafted or edited with the assistance of large language models. All content supported by AI is reviewed, checked for accuracy, and approved by a human team member before publication. AI is never used to generate unverified statistics, customer testimonials, or specific financial projections. We do not use AI to impersonate human authors. AI tools are used for initial research summaries, grammar and clarity improvements, and content formatting. A human verifies every substantive claim, data point, and recommendation.",
  },
  {
    heading: "Author and Company Credentials",
    body: `Pacific North Systems is a Canadian custom software and automation company based in Vancouver, BC. We build custom business applications, workflow automation, system integrations, document processing supported by AI, dashboards and reporting, and CRM systems for small and midsize businesses. Our team has experience in software engineering, business process analysis, and Canadian SMB operations. Contact: ${siteConfig.contact.email}. Location: ${siteConfig.contact.location}. We do not hold ourselves out as financial advisors, accountants, or legal professionals. Our tools and content are for informational and planning purposes only.`,
  },
  {
    heading: "Content Review and Maintenance",
    body: "Research pages state their publication date, next planned review, and version. We review source-dependent claims when the cited source changes, calculator language at least twice a year, and guides at least annually. Outdated pages are updated or clearly marked as archived.",
  },
  {
    heading: "Privacy and Ethics in Research",
    body: "We do not collect, store, or analyze personal data from calculator users unless they explicitly submit a contact form. We never include client data in published research without explicit written consent. We never publish testimonials that were not provided voluntarily with explicit publication consent. Our benchmark data is derived entirely from public sources; we do not claim a representative dataset of Canadian businesses. See our privacy policy for full details.",
  },
];

export default function MethodologyPage() {
  return (
    <>
      <Section variant="dark">
        <Container>
          <div className="max-w-[920px] mx-auto py-8">
            <Badge>About</Badge>
            <h1 className="font-heading text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-white mt-4 mb-3">
              Editorial Methodology & Standards
            </h1>
            <p className="text-pns-text-light text-[15px] leading-relaxed">
              How we research, write, cite, correct, and maintain the content on
              pacificnorthsystems.com.
            </p>
          </div>
        </Container>
      </Section>

      <Section>
        <Container className="max-w-[920px]">
          <div className="space-y-8">
            {sections.map((s, i) => (
              <div key={i}>
                <h2 className="font-heading font-semibold text-[18px] text-pns-text-primary mb-2">
                  {s.heading}
                </h2>
                <p className="text-[15px] text-pns-text-muted leading-relaxed">
                  {s.body}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-12 pt-8 border-t border-pns-assessment-input-border text-center">
            <p className="text-[14px] text-pns-text-muted">
              Questions about our methodology? Contact{" "}
              <a href={`mailto:${siteConfig.contact.email}`} className="underline hover:text-pns-text-primary">
                {siteConfig.contact.email}
              </a>{" "}
              with &ldquo;Methodology&rdquo; in the subject line.
            </p>
          </div>
        </Container>
      </Section>
    </>
  );
}
