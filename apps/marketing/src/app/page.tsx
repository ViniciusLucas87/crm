import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Custom Software for Operations-Heavy Businesses",
  description:
    "Pacific North Systems designs and builds practical custom software, workflow automation, and connected operational systems for businesses worldwide.",
};

const services = [
  {
    number: "01",
    title: "Custom operational software",
    description:
      "Web and mobile applications designed around the way your team actually works—from internal tools and portals to field systems and custom CRMs.",
    href: "/solutions#custom-business-software",
  },
  {
    number: "02",
    title: "Workflow automation",
    description:
      "Reliable workflows that reduce duplicate entry, organize approvals, connect existing tools, and keep work moving between teams.",
    href: "/solutions#workflow-automation",
  },
  {
    number: "03",
    title: "Data, reporting, and AI",
    description:
      "Clear dashboards, document processing, and carefully scoped AI tools that make business information easier to use.",
    href: "/solutions#business-dashboards",
  },
];

const principles = [
  "Understand the operation before recommending technology",
  "Start with a focused, useful first release",
  "Build for reliability, ownership, and long-term support",
];

export default function HomePage() {
  return (
    <>
      <section className="border-b border-black/8 bg-white">
        <Container>
          <div className="grid gap-14 py-20 lg:grid-cols-[1.35fr_0.65fr] lg:items-end lg:py-28">
            <div className="max-w-[820px]">
              <p className="mb-7 text-sm font-semibold uppercase tracking-[0.18em] text-pns-text-muted">
                Based in Vancouver · Working worldwide
              </p>
              <h1 className="text-[clamp(3rem,7vw,6.25rem)] font-semibold leading-[0.98] tracking-[-0.045em] text-pns-text-primary">
                Software built around how your business actually runs.
              </h1>
              <p className="mt-8 max-w-2xl text-lg leading-8 text-pns-text-muted sm:text-xl">
                We design and build operational software for businesses that
                have outgrown spreadsheets, disconnected tools, and manual
                processes.
              </p>
              <div className="mt-10 flex flex-col gap-3 sm:flex-row">
                <Button href="/contact" size="lg">
                  Discuss your project
                </Button>
                <Button href="/solutions" variant="outline" size="lg">
                  View our services
                </Button>
              </div>
            </div>

            <aside className="border-l border-black/10 pl-6 lg:pl-8">
              <p className="text-sm font-semibold text-pns-text-primary">
                We work with
              </p>
              <p className="mt-3 leading-7 text-pns-text-muted">
                Businesses of all kinds—from growing service companies to
                established organizations with complex operations. We work
                remotely with clients anywhere in the world.
              </p>
            </aside>
          </div>
        </Container>
      </section>

      <section className="border-b border-black/8 bg-white py-14 lg:py-20">
        <Container>
          <div className="grid gap-8 md:grid-cols-[180px_1fr] md:items-center lg:grid-cols-[220px_1fr] lg:gap-14">
            <div className="w-36 overflow-hidden bg-pns-soft-blue md:w-full">
              <Image
                src="/images/founder.jpg"
                alt="Vini Dias, founder of Pacific North Systems"
                width={440}
                height={440}
                className="aspect-square h-auto w-full object-cover object-top"
                priority
              />
            </div>
            <div className="max-w-4xl">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
                Founder-led delivery
              </p>
              <h2 className="mt-3 text-2xl font-semibold leading-tight tracking-[-0.025em] text-pns-text-primary sm:text-3xl">
                Your project is led by an experienced technical partner—not
                passed through layers of account management.
              </h2>
              <p className="mt-5 max-w-3xl leading-7 text-pns-text-muted">
                Pacific North Systems is led by Vini Dias, a former Electronic
                Arts Tech Lead with experience building internal tools,
                automation systems, production pipelines, and operational
                software. Clients work directly with the person responsible for
                understanding the problem and delivering the system.
              </p>
              <Link
                href="/about"
                className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-pns-text-primary"
              >
                About Pacific North Systems <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-pns-bg py-20 lg:py-28">
        <Container>
          <div className="grid gap-10 lg:grid-cols-[0.7fr_1.3fr]">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
                What we do
              </p>
              <h2 className="mt-4 max-w-md text-3xl font-semibold leading-tight tracking-[-0.025em] text-pns-text-primary sm:text-4xl">
                Practical systems for important operational work.
              </h2>
            </div>

            <div className="border-t border-black/12">
              {services.map((service) => (
                <Link
                  key={service.number}
                  href={service.href}
                  className="group grid gap-4 border-b border-black/12 py-8 sm:grid-cols-[56px_0.8fr_1.2fr_24px] sm:items-start"
                >
                  <span className="text-sm font-medium text-pns-text-muted">
                    {service.number}
                  </span>
                  <h3 className="text-xl font-semibold text-pns-text-primary">
                    {service.title}
                  </h3>
                  <p className="leading-7 text-pns-text-muted">
                    {service.description}
                  </p>
                  <ArrowRight
                    className="mt-1 h-5 w-5 text-pns-text-muted transition-transform group-hover:translate-x-1"
                    aria-hidden="true"
                  />
                </Link>
              ))}
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-[#07182b] py-20 text-white lg:py-28">
        <Container>
          <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-white/55">
                Selected work
              </p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-[-0.025em] sm:text-4xl">
                Tour operations and booking allocation system
              </h2>
              <p className="mt-6 max-w-xl leading-7 text-white/68">
                Pacific North Systems built a custom operations platform for
                Yellow Cap Tours to organize bookings from multiple channels,
                allocate passengers and vehicles, and improve visibility into
                daily operations.
              </p>
              <blockquote className="mt-8 border-l border-white/25 pl-5 text-lg leading-8 text-white/85">
                “The system they delivered was designed around how our business
                really works, not around generic software.”
              </blockquote>
              <p className="mt-4 text-sm text-white/55">
                Lucio Kniest · Owner, Yellow Cap Tours
              </p>
              <Link
                href="/work"
                className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-white hover:text-white/75"
              >
                Read about our work <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="relative min-h-[360px] overflow-hidden border border-white/15 bg-[#e9e6de] sm:min-h-[430px]">
              <Image
                src="/images/yellow-cap-tours.png"
                alt="Yellow Cap Tours"
                fill
                className="scale-[1.55] object-contain"
                sizes="(max-width: 1024px) 100vw, 55vw"
              />
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-28">
        <Container>
          <div className="grid gap-12 lg:grid-cols-2 lg:gap-24">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
                How we work
              </p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-[-0.025em] text-pns-text-primary sm:text-4xl">
                Clear thinking before code.
              </h2>
              <p className="mt-6 max-w-xl text-lg leading-8 text-pns-text-muted">
                We begin by understanding the process, the people involved, and
                the cost of the current problem. Then we design the smallest
                dependable system that can make a meaningful difference.
              </p>
              <Link
                href="/process"
                className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-pns-text-primary"
              >
                See our delivery process <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <ol className="border-t border-black/12">
              {principles.map((principle, index) => (
                <li
                  key={principle}
                  className="grid grid-cols-[44px_1fr] gap-4 border-b border-black/12 py-6"
                >
                  <span className="text-sm text-pns-text-muted">
                    0{index + 1}
                  </span>
                  <span className="font-medium leading-7 text-pns-text-primary">
                    {principle}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </Container>
      </section>

      <section className="border-t border-black/8 bg-pns-bg py-20 lg:py-24">
        <Container>
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-end">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-pns-text-muted">
                Start a conversation
              </p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-[-0.025em] text-pns-text-primary sm:text-5xl">
                Tell us where your operation is getting stuck.
              </h2>
            </div>
            <div className="flex flex-col items-start gap-3 sm:flex-row">
              <Button href={siteConfig.contact.calendlyAudit} size="lg">
                Book a consultation
              </Button>
              <Button href={`mailto:${siteConfig.contact.email}`} variant="outline" size="lg">
                Email us
              </Button>
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}
