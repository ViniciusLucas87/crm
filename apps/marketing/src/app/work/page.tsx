import type { Metadata } from "next";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "Our Work",
  description:
    "Selected custom software work from Pacific North Systems, including an operations and booking allocation system for Yellow Cap Tours.",
};

export default function WorkPage() {
  return (
    <>
      <section className="border-b border-black/8 bg-white py-20 lg:py-28">
        <Container>
          <div className="max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
              Selected work
            </p>
            <h1 className="mt-5 text-[clamp(3rem,7vw,5.5rem)] font-semibold leading-[1.02] tracking-[-0.04em] text-pns-text-primary">
              Systems built for the way a business really works.
            </h1>
            <p className="mt-8 max-w-2xl text-xl leading-8 text-pns-text-muted">
              We focus on the operational problem, the people using the system,
              and the measurable improvement the work needs to create.
            </p>
          </div>
        </Container>
      </section>

      <section className="bg-pns-bg py-20 lg:py-28">
        <Container>
          <article className="grid gap-12 lg:grid-cols-[0.75fr_1.25fr] lg:gap-20">
            <div className="relative aspect-[8/3] w-full max-w-[560px] justify-self-center overflow-hidden border border-black/10 bg-[#e9e6de] lg:justify-self-start">
              <Image
                src="/images/yellow-cap-tours.png"
                alt="Yellow Cap Tours"
                fill
                className="scale-[1.34] object-cover object-[56%_47%]"
                sizes="(max-width: 1024px) 100vw, 45vw"
                priority
              />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-pns-text-muted">
                Tourism and transportation
              </p>
              <h2 className="mt-4 text-3xl font-semibold tracking-[-0.025em] text-pns-text-primary sm:text-4xl">
                Yellow Cap Tours
              </h2>
              <p className="mt-2 text-lg text-pns-text-muted">
                Tour Operations & Booking Allocation System
              </p>

              <div className="mt-9 grid gap-8 sm:grid-cols-2">
                <div>
                  <h3 className="font-semibold text-pns-text-primary">The need</h3>
                  <p className="mt-3 leading-7 text-pns-text-muted">
                    Organize bookings arriving from multiple tourism platforms,
                    coordinate passengers, schedules, and vehicle capacity, and
                    reduce reliance on manual processes.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold text-pns-text-primary">The result</h3>
                  <p className="mt-3 leading-7 text-pns-text-muted">
                    A custom system shaped around the company’s real operating
                    model, with clearer daily visibility and a simpler booking
                    workflow.
                  </p>
                </div>
              </div>

              <blockquote className="mt-10 border-l-2 border-pns-text-primary pl-6 text-xl leading-9 text-pns-text-primary">
                “It simplified our booking process, reduced manual work, and
                gave us much better visibility into our daily operations.”
              </blockquote>
              <p className="mt-4 text-sm text-pns-text-muted">
                Lucio Kniest · Owner, Yellow Cap Tours
              </p>
            </div>
          </article>
        </Container>
      </section>

      <section className="border-t border-black/8 bg-white py-20">
        <Container>
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-semibold tracking-[-0.025em] text-pns-text-primary">
                Your operation will not look exactly like this one.
              </h2>
              <p className="mt-4 text-lg leading-8 text-pns-text-muted">
                That is the point. We build around the specific workflow,
                constraints, and goals of each business.
              </p>
            </div>
            <Button href="/contact" size="lg">Discuss your project</Button>
          </div>
        </Container>
      </section>
    </>
  );
}
