import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, FileText, Calculator } from "lucide-react";

export const metadata: Metadata = {
  title: "Research | Canadian SMB Operations Data | Pacific North Systems",
  description:
    "Transparent, citation-backed research on Canadian small business operations, automation costs, and workflow benchmarks. All data sourced from Statistics Canada and Government of Canada public data.",
  alternates: { canonical: "https://www.pacificnorthsystems.com/research" },
};

export default function ResearchHub() {
  return (
    <>
      <Section variant="dark">
        <Container>
          <div className="flex flex-col items-center text-center max-w-3xl mx-auto py-8">
            <Badge>Research</Badge>
            <h1 className="font-heading text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-white mt-4 mb-3">
              Canadian SMB Operations Research
            </h1>
            <p className="text-pns-text-light text-[15px] leading-relaxed max-w-xl">
              Transparent, citation-backed benchmarks and analysis for Canadian
              small and midsize business operations. All data sourced from
              verified public sources with inline citations.
            </p>
          </div>
        </Container>
      </Section>

      <Section>
        <Container>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <Link href="/research/manual-work-cost-benchmark-2026">
              <Card className="h-full hover:shadow-md transition-shadow p-6" variant="elevated">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-[#051226] mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-heading font-semibold text-[16px] text-pns-text-primary mb-2">
                      Canadian SMB Manual Work Cost Planning Baseline, 2026
                    </h3>
                    <p className="text-[14px] text-pns-text-muted leading-relaxed mb-3">
                      A planning baseline for estimating manual work costs in
                      Canadian SMBs, built from official Canadian business data
                      and cost assumptions supplied by the owner. Not a survey and not
                      a claim of achieved savings.
                    </p>
                    <span className="text-[13px] font-medium text-pns-text-primary inline-flex items-center gap-1">
                      Read benchmark <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </Card>
            </Link>

            <Link href="/free-tools/manual-work-cost-calculator">
              <Card className="h-full hover:shadow-md transition-shadow p-6" variant="elevated">
                <div className="flex items-start gap-3">
                  <Calculator className="w-5 h-5 text-[#051226] mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-heading font-semibold text-[16px] text-pns-text-primary mb-2">
                      Manual Work Cost Calculator
                    </h3>
                    <p className="text-[14px] text-pns-text-muted leading-relaxed mb-3">
                      Apply the benchmark data to your own business. Free,
                      client-side calculator with methodology notes and
                      assumptions explained. No signup required.
                    </p>
                    <span className="text-[13px] font-medium text-pns-text-primary inline-flex items-center gap-1">
                      Open calculator <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </Card>
            </Link>
          </div>

          <div className="max-w-3xl mx-auto mt-12 p-6 bg-pns-soft-blue rounded-[16px]">
            <h2 className="font-heading font-semibold text-[18px] text-pns-text-primary mb-3">
              Our Research Standards
            </h2>
            <ul className="space-y-2 text-[14px] text-pns-text-muted leading-relaxed">
              <li>• Factual Canadian data uses named primary public sources with direct links and reference dates.</li>
              <li>• We clearly distinguish between published public data and our own calculator scenarios or methodology assumptions.</li>
              <li>• We never invent customer numbers, survey sample sizes, savings claims, business names, testimonials, or results.</li>
              <li>• If a precise statistic cannot be verified, we omit it rather than estimate it without attribution.</li>
              <li>• Each research page includes: methodology, formulas, limitations, last-reviewed date, version, worked examples, source list, and quotable findings.</li>
            </ul>
            <Link href="/methodology" className="inline-flex items-center gap-1 text-[14px] font-medium text-pns-text-primary mt-4 hover:underline">
              Read our full editorial methodology <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </Container>
      </Section>
    </>
  );
}
