import type { Metadata } from "next";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "How We Work",
  description:
    "A clear, practical process for designing, building, and supporting custom operational software.",
  alternates: { canonical: "/process" },
};

const phases = [
  {
    number: "01",
    title: "Understand",
    subtitle: "Operations audit",
    body: "We review the current workflow with the people who perform it. We document where information begins, where it is copied, where it waits, and what happens when something goes wrong.",
    output: "A clear problem statement, current-state workflow, and priorities.",
  },
  {
    number: "02",
    title: "Design",
    subtitle: "System plan",
    body: "We define the improved workflow, the information the system must manage, and the smallest useful first release. Important assumptions and tradeoffs remain visible.",
    output: "A proposed workflow, delivery scope, and implementation plan.",
  },
  {
    number: "03",
    title: "Build",
    subtitle: "Focused delivery",
    body: "We develop the system in reviewable stages, test it with realistic scenarios, and incorporate feedback from the people who will use it.",
    output: "Working software with training and operational documentation.",
  },
  {
    number: "04",
    title: "Improve",
    subtitle: "Support and iteration",
    body: "After launch, we monitor the system, resolve issues, and prioritize improvements using real usage and business feedback rather than assumptions.",
    output: "A supported system that can evolve with the operation.",
  },
];

export default function ProcessPage() {
  return (
    <>
      <section className="border-b border-black/8 bg-white py-20 lg:py-28">
        <Container>
          <div className="max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
              How we work
            </p>
            <h1 className="mt-5 text-[clamp(3rem,7vw,5.5rem)] font-semibold leading-[1.02] tracking-[-0.04em] text-pns-text-primary">
              A disciplined path from operational problem to dependable system.
            </h1>
            <p className="mt-8 max-w-2xl text-xl leading-8 text-pns-text-muted">
              Every engagement is shaped around the business, but the underlying
              approach stays consistent: understand first, keep the scope clear,
              and prove value through working software.
            </p>
          </div>
        </Container>
      </section>

      <section className="bg-pns-bg py-20 lg:py-28">
        <Container>
          <div className="border-t border-black/12">
            {phases.map((phase) => (
              <article
                key={phase.number}
                className="grid gap-5 border-b border-black/12 py-10 md:grid-cols-[70px_0.65fr_1.1fr_0.8fr] md:gap-8"
              >
                <span className="text-sm font-medium text-pns-text-muted">
                  {phase.number}
                </span>
                <div>
                  <h2 className="text-2xl font-semibold text-pns-text-primary">
                    {phase.title}
                  </h2>
                  <p className="mt-1 text-sm text-pns-text-muted">{phase.subtitle}</p>
                </div>
                <p className="leading-7 text-pns-text-muted">{phase.body}</p>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-pns-text-muted">
                    Outcome
                  </p>
                  <p className="mt-2 leading-7 text-pns-text-primary">{phase.output}</p>
                </div>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="bg-[#07182b] py-20 text-white">
        <Container>
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-semibold tracking-[-0.025em] sm:text-4xl">
                Have a process that needs a better system?
              </h2>
              <p className="mt-4 text-lg leading-8 text-white/65">
                We can review it with you and help determine whether custom
                software is the right next step.
              </p>
            </div>
            <Button href="/contact" size="lg" className="bg-white !text-[#07182b] hover:bg-white/90">
              Start a conversation
            </Button>
          </div>
        </Container>
      </section>
    </>
  );
}
