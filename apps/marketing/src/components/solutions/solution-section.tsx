import { cn } from "@/lib/cn";
import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface SolutionSectionData {
  id: string;
  icon: LucideIcon;
  title: string;
  problem: string;
  whenUseful: string;
  whoNeedsIt: string;
  useCases: string[];
  exampleWorkflow: string;
  typicalFirstVersion: string;
  expectedOutcome: string;
  relevantIndustries: string[];
}

interface SolutionSectionProps {
  data: SolutionSectionData;
  index: number;
}

export function SolutionSection({ data, index }: SolutionSectionProps) {
  const isEven = index % 2 === 0;

  return (
    <section
      id={data.id}
      className={cn(
        "py-16 lg:py-20 scroll-mt-24",
        isEven ? "bg-white" : "bg-pns-soft-blue",
      )}
    >
      <div className="mx-auto max-w-[1440px] px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          {/* Icon + Title */}
          <div className="flex items-center gap-3 mb-6">
            <data.icon
              className="w-8 h-8 text-pns-text-muted"
              aria-hidden="true"
            />
            <h2 className="text-2xl lg:text-3xl font-bold text-pns-text-primary">
              {data.title}
            </h2>
          </div>

          {/* Problem */}
          <p className="text-pns-text-muted leading-relaxed">{data.problem}</p>

          {/* Grid of details */}
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <DetailBlock title="When it's useful" content={data.whenUseful} />
            <DetailBlock title="Who needs it" content={data.whoNeedsIt} />
          </div>

          {/* Use cases */}
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-pns-text-primary uppercase tracking-wide">
              Use cases
            </h4>
            <ul className="mt-3 space-y-2">
              {data.useCases.map((uc) => (
                <li
                  key={uc}
                  className="flex items-start gap-2 text-sm text-pns-text-muted"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-pns-text-muted shrink-0" />
                  {uc}
                </li>
              ))}
            </ul>
          </div>

          {/* Example workflow */}
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-pns-text-primary uppercase tracking-wide">
              Example workflow
            </h4>
            <p className="mt-2 text-sm text-pns-text-muted leading-relaxed">
              {data.exampleWorkflow}
            </p>
          </div>

          {/* Typical first version */}
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-pns-text-primary uppercase tracking-wide">
              Typical first version
            </h4>
            <p className="mt-2 text-sm text-pns-text-muted leading-relaxed">
              {data.typicalFirstVersion}
            </p>
          </div>

          {/* Expected outcome */}
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-pns-text-primary uppercase tracking-wide">
              Expected outcome
            </h4>
            <p className="mt-2 text-sm text-pns-text-muted leading-relaxed">
              {data.expectedOutcome}
            </p>
          </div>

          {/* Industries */}
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-pns-text-primary uppercase tracking-wide">
              Relevant industries
            </h4>
            <div className="mt-2 flex flex-wrap gap-2">
              {data.relevantIndustries.map((ind) => (
                <span
                  key={ind}
                  className="inline-flex items-center rounded-full border border-pns-text-primary/15 px-3 py-1 text-xs text-pns-text-muted"
                >
                  {ind}
                </span>
              ))}
            </div>
          </div>

          {/* Assessment CTA */}
          <div className="mt-10 pt-8 border-t border-pns-text-primary/10 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div>
              <p className="text-sm font-medium text-pns-text-primary">
                Not sure where to begin?
              </p>
              <p className="text-sm text-pns-text-muted">
                Use the Business Automation Assessment to identify your biggest
                opportunity.
              </p>
            </div>
            <Button variant="secondary" size="sm" href="/assessment">
              Take Assessment
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

function DetailBlock({
  title,
  content,
}: {
  title: string;
  content: string;
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-pns-text-primary uppercase tracking-wide">
        {title}
      </h4>
      <p className="mt-2 text-sm text-pns-text-muted leading-relaxed">
        {content}
      </p>
    </div>
  );
}
