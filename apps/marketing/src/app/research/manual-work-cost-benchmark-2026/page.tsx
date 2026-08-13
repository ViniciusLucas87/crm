import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "Canadian SMB Manual Work Cost Planning Baseline, 2026 | Pacific North Systems",
  description:
    "A planning baseline for estimating manual work costs in Canadian SMBs using official Canadian data and assumptions supplied by business owners. Not a representative national survey.",
  alternates: {
    canonical: "https://pacificnorthsystems.com/research/manual-work-cost-benchmark-2026",
  },
};

/* ------------------------------------------------------------------ */
/*  Quotable factual findings (all sourced)                            */
/* ------------------------------------------------------------------ */

const findings = [
  {
    finding:
      "Statistics Canada publishes employee wage distributions by occupation, including median hourly wages. Use the current table filters for geography, occupation, age, sex, and job characteristics rather than treating one national value as universal.",
    source: "Statistics Canada, Employee wages by occupation, Table 14-10-0340-01",
    sourceUrl:
      "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410034001",
  },
  {
    finding:
      "Canadian small businesses (1-99 employees) numbered approximately 1.2 million in 2023, representing 98% of all employer businesses in Canada.",
    source:
      "Innovation, Science and Economic Development Canada, Key Small Business Statistics 2023",
    sourceUrl:
      "https://ised-isde.canada.ca/site/sme-research-statistics/en/key-small-business-statistics/key-small-business-statistics-2023",
  },
  {
    finding:
      "Vacation and statutory-holiday entitlements depend on the applicable federal or provincial employment standard. Calculator users should enter the working weeks that match their own organization rather than relying on a national default.",
    source: "Government of Canada, Federal labour standards",
    sourceUrl: "https://www.canada.ca/en/employment-social-development/programs/employment-standards.html",
  },
];

/* ------------------------------------------------------------------ */
/*  Methodology section                                                 */
/* ------------------------------------------------------------------ */

const methodology = [
  {
    heading: "What This Benchmark Is",
    body: "This page provides a planning baseline for estimating manual work costs in Canadian small and midsize businesses (SMBs). It is intended for business planning and rough cost estimation. It is not a representative national survey, a statistically sampled study, or a market research report. No survey was conducted and no customer data was used.",
  },
  {
    heading: "What This Benchmark Is Not",
    body: "This is not a survey of Pacific North Systems customers. It is not a representative sample of Canadian businesses. It does not reflect actual savings achieved by any specific company. It does not include proprietary or confidential data. No testimonials, case studies, or individual business results are implied by these figures.",
  },
  {
    heading: "Data Sources and Citation Policy",
    body: "Published facts on this page link directly to Statistics Canada or Government of Canada sources. PNS calculator defaults and hypothetical scenarios are identified separately as planning assumptions. When a precise statistic cannot be verified from a primary source, we omit it rather than present it as a benchmark.",
  },
  {
    heading: "Calculator Methodology",
    body: "Our free manual work cost calculator, linked below, applies the benchmark wage and burden data to inputs provided by the user: number of employees affected, hours per week spent on the task, loaded hourly cost, working weeks per year, and estimated recoverable percentage. The calculator formula is: Annual Manual Cost = Employees × Hours/Week × Loaded Hourly Rate × Weeks/Year. Recoverable Cost = Annual Cost × Recoverable Percentage. These are directional estimates for business planning. Actual savings depend on implementation quality, process standardization, and employee adoption.",
  },
  {
    heading: "Loaded Hourly Rate Calculation",
    body: "Loaded hourly cost can include base wages, employer payroll contributions, benefits, workers' compensation, equipment, workspace, and management overhead. These amounts vary by year, province, industry, benefit plan, and employer. PNS does not prescribe a universal multiplier: users should calculate or obtain their own loaded hourly cost and enter it directly.",
  },
  {
    heading: "Recoverable Percentage",
    body: "The recoverable percentage is a user-adjustable PNS planning assumption, not a published Canadian benchmark. It represents the portion of measured task time a proposed change might reduce. Validate it with a small pilot and replace the assumption with observed before-and-after results before approving an investment.",
  },
  {
    heading: "Limitations",
    body: "This baseline cannot account for industry and regional wage differences, organization-specific overhead, implementation and operating costs, training or process redesign, adoption, failures, or economic change. Use the current source filters and your own records. It is a starting point for analysis, not a prediction.",
  },
  {
    heading: "Version and Updates",
    body: "Version: 1.0. Published and last reviewed: August 3, 2026. Next scheduled review: February 1, 2027, or earlier when a cited source is materially revised. The version number increments with substantive methodology or source changes, not cosmetic edits.",
  },
];

export default function BenchmarkPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Canadian Small Business Manual Work Cost Planning Baseline, 2026",
    description:
      "A planning baseline for estimating manual work costs in Canadian SMBs, built from Statistics Canada data. Not a survey; methodology clearly labelled.",
    author: { "@type": "Organization", name: "Pacific North Systems" },
    datePublished: "2026-08-03",
    dateModified: "2026-08-03",
    publisher: { "@type": "Organization", name: "Pacific North Systems" },
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": "https://pacificnorthsystems.com/research/manual-work-cost-benchmark-2026",
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <Section variant="dark">
        <Container>
          <div className="max-w-[920px] mx-auto py-8">
            <Link
              href="/research"
              className="inline-flex items-center gap-1 text-[14px] text-pns-text-light hover:text-white transition-colors mb-4"
            >
              ← Research hub
            </Link>
            <Badge>Research · Planning Baseline</Badge>
            <h1 className="font-heading text-[clamp(1.5rem,3.5vw,2.25rem)] font-bold text-white mt-3 mb-3">
              Canadian Small Business Manual Work Cost Planning Baseline, 2026
            </h1>
            <p className="text-pns-text-light text-[15px] leading-relaxed">
              A planning baseline for estimating manual work costs in Canadian
              SMBs. All data from verified public sources. Not a representative
              national survey.
            </p>
            <p className="text-pns-text-light/60 text-[13px] mt-3">
              Version 1.0 · Published August 3, 2026 · Next review: February 1, 2027
            </p>
          </div>
        </Container>
      </Section>

      <Section>
        <Container className="max-w-[920px]">
          {/* Key Findings */}
          <h2 className="font-heading font-semibold text-[22px] text-pns-text-primary mb-6">
            Quotable Findings
          </h2>

          <div className="space-y-4 mb-12">
            {findings.map((f, i) => (
              <div key={i} className="border border-pns-assessment-input-border rounded-[12px] p-5">
                <p className="text-[15px] text-pns-text-primary leading-relaxed mb-2">
                  {f.finding}
                </p>
                <p className="text-[13px] text-pns-text-muted">
                  Source:{" "}
                  <a
                    href={f.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-pns-text-primary transition-colors"
                  >
                    {f.source}
                  </a>
                </p>
              </div>
            ))}
          </div>

          {/* Methodology */}
          <h2 className="font-heading font-semibold text-[22px] text-pns-text-primary mb-6">
            Methodology
          </h2>

          <div className="space-y-8 mb-12">
            {methodology.map((section, i) => (
              <div key={i}>
                <h3 className="font-heading font-semibold text-[17px] text-pns-text-primary mb-2">
                  {section.heading}
                </h3>
                <p className="text-[15px] text-pns-text-muted leading-relaxed">
                  {section.body}
                </p>
              </div>
            ))}
          </div>

          <section className="mb-12 rounded-[16px] border border-pns-assessment-input-border p-6">
            <h2 className="font-heading font-semibold text-[22px] text-pns-text-primary mb-3">
              Hypothetical worked example
            </h2>
            <p className="text-[15px] text-pns-text-muted leading-relaxed">
              A hypothetical team of four records 3 hours per person each week on a
              repetitive task. The owner supplies a loaded cost of $40 per hour and
              uses 48 working weeks. The planning calculation is 4 × 3 × $40 × 48 =
              $23,040 of annual task cost. If a pilot later demonstrates that 25% of
              that time can be removed, the observed planning value would be $5,760
              per year. This is an illustration, not a customer result or promise of
              savings; implementation cost and ongoing operating cost must be assessed
              separately.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="font-heading font-semibold text-[22px] text-pns-text-primary mb-3">
              Quarterly data roadmap and privacy threshold
            </h2>
            <p className="text-[15px] text-pns-text-muted leading-relaxed mb-3">
              PNS does not currently claim a representative calculator dataset. A
              future quarterly edition may publish aggregate ranges only from records
              whose users separately consent to research use. Contact details, free
              text, company names, IP addresses, and exact records will not be included.
            </p>
            <p className="text-[15px] text-pns-text-muted leading-relaxed">
              Our proposed publication policy suppresses any segment with fewer than
              20 consented observations and reports ranges or medians rather than raw
              rows. Each release will document its date range, sample source, inclusion
              rules, missing data, geographic coverage, version, and limitations. This
              threshold is a PNS privacy policy choice, not a claim of statistical
              representativeness.
            </p>
          </section>

          <section className="mb-12 border-t border-pns-assessment-input-border pt-8">
            <h2 className="font-heading font-semibold text-[22px] text-pns-text-primary mb-3">
              Review and corrections
            </h2>
            <p className="text-[15px] text-pns-text-muted leading-relaxed">
              Prepared and reviewed by the Pacific North Systems editorial team.
              Version 1.0 was published August 3, 2026. No corrections have been logged.
              See our <Link href="/methodology" className="underline">editorial methodology</Link>,
              or email <a href="mailto:hello@pacificnorthsystems.com?subject=Correction%20request" className="underline">hello@pacificnorthsystems.com</a> with the source and proposed correction.
            </p>
          </section>

          {/* CTA */}
          <div className="bg-pns-soft-blue rounded-[16px] p-6 text-center">
            <h3 className="font-heading font-semibold text-[18px] text-pns-text-primary mb-2">
              Apply this data to your business
            </h3>
            <p className="text-[14px] text-pns-text-muted mb-4">
              Use our free calculator with your own team size, observed task
              time, loaded cost, working weeks, and pilot result.
            </p>
            <Link href="/free-tools/manual-work-cost-calculator">
              <Button>
                Open Manual Work Cost Calculator
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </Container>
      </Section>
    </>
  );
}
