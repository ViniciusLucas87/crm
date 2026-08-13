import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "About",
  description:
    "Learn about Pacific North Systems, a custom software company led by its founder, based in Vancouver and serving clients worldwide.",
};

const values = [
  {
    title: "Understand the real work",
    body: "Good software starts with the people, decisions, constraints, and exceptions inside an operation, not with a list of fashionable features.",
  },
  {
    title: "Keep the solution practical",
    body: "We prefer focused systems that people can understand, adopt, and maintain over unnecessary complexity.",
  },
  {
    title: "Stay accountable",
    body: "Clear communication, visible decisions, honest tradeoffs, and dependable support are part of the engineering work.",
  },
];

export default function AboutPage() {
  return (
    <>
      <section className="border-b border-black/8 bg-white py-20 lg:py-28">
        <Container>
          <div className="max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
              About Pacific North Systems
            </p>
            <h1 className="mt-5 text-[clamp(3rem,7vw,5.5rem)] font-semibold leading-[1.02] tracking-[-0.04em] text-pns-text-primary">
              Technical experience, grounded in real operations.
            </h1>
            <p className="mt-8 max-w-2xl text-xl leading-8 text-pns-text-muted">
              Pacific North Systems is based in Vancouver and works with
              businesses worldwide to replace fragmented processes with clear,
              reliable systems.
            </p>
          </div>
        </Container>
      </section>

      <section className="bg-pns-bg py-20 lg:py-28">
        <Container>
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-center lg:gap-20">
            <div className="overflow-hidden bg-pns-soft-blue">
              <Image
                src="/images/founder.jpg"
                alt="Vini Dias, founder of Pacific North Systems"
                width={720}
                height={900}
                className="aspect-[4/5] h-auto w-full object-cover"
                priority
              />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
                Founder led
              </p>
              <h2 className="mt-4 text-3xl font-semibold tracking-[-0.025em] text-pns-text-primary sm:text-4xl">
                Direct access to the person responsible for the work.
              </h2>
              <div className="mt-7 space-y-5 text-lg leading-8 text-pns-text-muted">
                <p>
                  Pacific North Systems is led by Vini Dias, a former Electronic
                  Arts Tech Lead with experience building internal tools,
                  automation systems, production pipelines, and developer
                  productivity software.
                </p>
                <p>
                  That technical background is combined with practical,
                  hands-on experience in field operations. The result is a
                  straightforward approach: understand the work, identify the
                  constraint, and build the right system for the business.
                </p>
              </div>
              <Link
                href="/process"
                className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-pns-text-primary"
              >
                How we deliver projects <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-28">
        <Container>
          <div className="grid gap-10 lg:grid-cols-[0.65fr_1.35fr]">
            <h2 className="text-3xl font-semibold tracking-[-0.025em] text-pns-text-primary">
              Working principles
            </h2>
            <div className="border-t border-black/12">
              {values.map((value, index) => (
                <div
                  key={value.title}
                  className="grid gap-3 border-b border-black/12 py-7 sm:grid-cols-[44px_0.8fr_1.2fr]"
                >
                  <span className="text-sm text-pns-text-muted">0{index + 1}</span>
                  <h3 className="font-semibold text-pns-text-primary">{value.title}</h3>
                  <p className="leading-7 text-pns-text-muted">{value.body}</p>
                </div>
              ))}
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}
