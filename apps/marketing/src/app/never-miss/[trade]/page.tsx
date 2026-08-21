import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, PhoneMissed } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { neverMissTradeSlugs, neverMissTradeSolutions } from "@/lib/never-miss-trades";

type Props = {
  params: Promise<{ trade: string }>;
};

const checkoutAvailable = Boolean(process.env.NEVER_MISS_FREE_TRIAL_URL);

export async function generateStaticParams() {
  return neverMissTradeSlugs.map((trade) => ({ trade }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { trade } = await params;
  const solution = neverMissTradeSolutions[trade];
  if (!solution) return { title: "Not Found" };

  return {
    title: { absolute: solution.seoTitle },
    description: solution.description,
    alternates: { canonical: `/never-miss/${solution.slug}` },
    openGraph: {
      title: solution.seoTitle,
      description: solution.description,
      url: `/never-miss/${solution.slug}`,
      images: [{ url: "/images/never-miss-step-call.png", alt: "A business phone call that needs a follow-up" }],
    },
  };
}

export default async function NeverMissTradePage({ params }: Props) {
  const { trade } = await params;
  const solution = neverMissTradeSolutions[trade];
  if (!solution) notFound();

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: solution.faq.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: { "@type": "Answer", text: item.answer },
    })),
  };

  const ctaHref = checkoutAvailable ? "/never-miss/checkout?plan=never-miss" : "/contact";
  const ctaLabel = checkoutAvailable ? "Start your 30-day free test" : "Talk to our team";

  return (
    <main>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
      <section className="bg-[#071729] py-16 text-white sm:py-20">
        <Container>
          <Link href="/never-miss" className="inline-flex items-center gap-2 text-sm text-cyan-200 hover:text-white">
            <ArrowLeft className="h-4 w-4" /> Never Miss
          </Link>
          <div className="mt-10 grid gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">{solution.eyebrow}</p>
              <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">{solution.hero}</h1>
              <p className="mt-6 text-lg leading-8 text-white/80">{solution.problem}</p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Button href={ctaHref} size="lg" className="bg-cyan-300 !text-[#071729] hover:bg-cyan-200">{ctaLabel} <ArrowRight className="h-4 w-4" /></Button>
                <Link href="#setup" className="text-sm font-semibold text-cyan-200 hover:text-white">See the setup checks</Link>
              </div>
              <p className="mt-4 text-sm text-white/65">{checkoutAvailable ? "No charge today. Cancel before 30 days to avoid the first monthly charge." : "Online trial enrolment is temporarily unavailable. We will not take payment until self-service checkout is ready."}</p>
            </div>
            <div className="relative aspect-[4/3] overflow-hidden rounded-3xl border border-white/15 bg-slate-800 shadow-2xl">
              <Image src="/images/never-miss-contractor-hero.gif" alt="A service contractor checking a customer message while working" fill priority unoptimized sizes="(min-width: 1024px) 45vw, 100vw" className="object-cover" />
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-16 sm:py-20">
        <Container>
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">A focused handoff</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary sm:text-4xl">Acknowledge the caller. Keep the callback visible.</h2>
            <p className="mt-5 text-lg leading-8 text-pns-text-muted">{solution.example}</p>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {solution.fitPoints.map((point, index) => (
              <article key={point} className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                <p className="text-sm font-semibold text-[#0b6575]">0{index + 1}</p>
                <p className="mt-3 leading-7 text-pns-text-primary">{point}</p>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section id="setup" className="bg-[#edf5f5] py-16 sm:py-20">
        <Container>
          <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <div>
              <PhoneMissed className="h-9 w-9 text-[#0b6575]" />
              <p className="mt-5 text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Before customer use</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary">Set it up carefully, then test the real workflow.</h2>
              <p className="mt-5 leading-7 text-pns-text-muted">Carrier forwarding, delivery, and callback creation must work together. A health check alone cannot confirm that a real customer call will follow the intended path.</p>
            </div>
            <ol className="space-y-4">
              {solution.setupPoints.map((point, index) => (
                <li key={point} className="flex gap-4 rounded-2xl bg-white p-5 shadow-sm">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#071729] text-sm font-semibold text-cyan-200">{index + 1}</span>
                  <span className="leading-7 text-pns-text-primary">{point}</span>
                </li>
              ))}
            </ol>
          </div>
        </Container>
      </section>

      <section className="bg-white py-16 sm:py-20">
        <Container size="narrow">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Questions before you start</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary">Common questions from {solution.title.toLowerCase()}</h2>
          <div className="mt-8 space-y-3">
            {solution.faq.map((item) => (
              <details key={item.question} className="rounded-2xl border border-slate-200 bg-white p-5">
                <summary className="cursor-pointer font-semibold text-pns-text-primary">{item.question}</summary>
                <p className="mt-3 leading-7 text-pns-text-muted">{item.answer}</p>
              </details>
            ))}
          </div>
          <div className="mt-12 rounded-3xl bg-[#071729] p-7 text-white sm:p-9">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
              <div><h2 className="text-2xl font-semibold">Start with the missed calls you already receive.</h2><p className="mt-2 max-w-2xl leading-7 text-white/75">Keep your business number. Use unanswered-call forwarding only. Confirm the full flow before you rely on it.</p></div>
              <Button href={ctaHref} size="lg" className="shrink-0 bg-cyan-300 !text-[#071729] hover:bg-cyan-200">{ctaLabel} <ArrowRight className="h-4 w-4" /></Button>
            </div>
            <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-sm text-white/70"><span className="inline-flex items-center gap-2"><Check className="h-4 w-4 text-cyan-300" />30 days free</span><span className="inline-flex items-center gap-2"><Check className="h-4 w-4 text-cyan-300" />Cancel anytime</span><Link href="/never-miss" className="text-cyan-200 hover:text-white">See the full Never Miss workflow</Link></div>
          </div>
          <div className="mt-10 rounded-2xl border border-slate-200 bg-slate-50 p-6"><h2 className="text-xl font-semibold text-pns-text-primary">Helpful next reading</h2><ul className="mt-4 space-y-3 text-[#0b6575]"><li><Link className="hover:underline" href="/blog/what-happens-when-a-contractor-misses-a-customer-call">What happens when a contractor misses a customer call?</Link></li><li><Link className="hover:underline" href="/blog/what-should-a-contractor-say-in-a-missed-call-text">What should a contractor say in a missed-call text?</Link></li><li><Link className="hover:underline" href="/blog/how-contractors-can-prioritize-callbacks">How contractors can prioritize callbacks</Link></li></ul></div>
        </Container>
      </section>
    </main>
  );
}
