import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";

const steps = [
  {
    number: "01",
    title: "Operations Audit",
    description: "We learn your business and identify the biggest time drains.",
  },
  {
    number: "02",
    title: "Workflow Map",
    description: "We map the process and design a better way to work.",
  },
  {
    number: "03",
    title: "MVP Build",
    description: "We build a focused solution, test, and iterate quickly.",
  },
  {
    number: "04",
    title: "Deploy & Improve",
    description: "We deploy, train your team, and keep improving.",
  },
];

export function Process() {
  return (
    <Section variant="default" id="process">
      <Container>
        <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary text-center">
          How we work
        </h2>

        <div className="mt-14 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step) => (
            <div key={step.number} className="text-center lg:text-left">
              <span className="text-4xl font-bold text-pns-accent-light">
                {step.number}
              </span>
              <h3 className="mt-3 font-bold text-pns-text-primary text-lg">
                {step.title}
              </h3>
              <p className="mt-2 text-sm text-pns-text-muted leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
