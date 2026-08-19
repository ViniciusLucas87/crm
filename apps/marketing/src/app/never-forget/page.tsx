import type { Metadata } from "next";
import Image from "next/image";
import {
  ArrowRight,
  BellRing,
  CalendarCheck,
  Check,
  FileCheck2,
  LockKeyhole,
  MessageSquareText,
  ShieldCheck,
  Wrench,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "Never Forget | Service Records That Bring Customers Back",
  description:
    "Give every customer a clear service record, warranty details, care instructions, and a simple way to call you for the next job.",
  alternates: { canonical: "/never-forget" },
};

const workflow = [
  {
    icon: Wrench,
    number: "01",
    title: "Finish the job",
    copy: "Add what you fixed, the parts you used, the warranty, and any care instructions.",
  },
  {
    icon: MessageSquareText,
    number: "02",
    title: "Send one simple link",
    copy: "Your customer opens their private service record. There is no app to download and no account to create.",
  },
  {
    icon: BellRing,
    number: "03",
    title: "Be there for the next job",
    copy: "When service is due, the customer remembers who did the work and can ask you to come back.",
  },
];

const trades = [
  "HVAC and heating",
  "Plumbing",
  "Electrical",
  "Appliance repair",
  "Garage doors",
  "Equipment service",
  "Property maintenance",
  "Home inspections",
];

export default function NeverForgetPage() {
  return (
    <main>
      <section className="relative min-h-[720px] overflow-hidden bg-[#071729] text-white">
        <Image
          src="/images/never-forget-contractor-hero.png"
          alt="A contractor showing a homeowner her digital service record after finishing an HVAC job"
          fill
          priority
          sizes="100vw"
          className="object-cover object-[67%_center] sm:object-[64%_center] lg:object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#071729]/25 via-transparent to-[#071729]/80 lg:bg-gradient-to-r lg:from-[#071729] lg:from-[0%] lg:via-[#071729]/95 lg:via-[39%] lg:to-transparent lg:to-[68%]" />
        <Container className="relative z-10 flex min-h-[720px] items-end py-14 sm:py-16 lg:items-center lg:py-20">
          <div className="max-w-2xl rounded-3xl bg-[#071729]/88 p-6 backdrop-blur-[2px] sm:p-8 lg:max-w-[47%] lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">
              Built for service businesses
            </p>
            <h1 className="mt-5 text-[clamp(2.8rem,11vw,5.4rem)] font-semibold leading-[0.94] tracking-[-0.045em] lg:text-[clamp(3.4rem,5.5vw,5.5rem)]">
              Finish the job. Stay remembered.
            </h1>
            <p className="mt-7 max-w-xl text-xl leading-8 text-white/85">
              Give every customer a clear record of the work, their warranty, and when to call you again.
            </p>
            <p className="mt-4 font-semibold text-white">
              No app for the customer. No paper to lose. No forgotten contractor.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button
                href="/contact?product=never-forget"
                size="lg"
                className="w-full bg-cyan-300 !text-[#071729] hover:bg-cyan-200 sm:w-auto"
              >
                Join the contractor pilot <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                href="#how-it-works"
                variant="outline"
                size="lg"
                className="w-full border-white/40 !text-white hover:bg-white/10 sm:w-auto"
              >
                See how it works
              </Button>
            </div>
            <p className="mt-4 text-sm text-white/65">Small Canadian pilot. We help you set it up.</p>
          </div>
        </Container>
      </section>

      <section className="bg-[#f4f7f7] py-20 lg:py-24">
        <Container>
          <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">
                The job is done. The relationship is not.
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
                Good work should lead to the next call.
              </h2>
              <p className="mt-5 text-lg leading-8 text-pns-text-muted">
                Customers forget who installed the unit, where the receipt went, and when it needs service. When the next problem appears, they search again and somebody else gets the job.
              </p>
              <p className="mt-4 text-lg font-semibold leading-8 text-pns-text-primary">
                Never Forget keeps your name attached to the work you already earned.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                [FileCheck2, "One clear record", "Work, parts, warranty, photos, and care notes stay together."],
                [CalendarCheck, "The right date", "Your recommended service date does not disappear in a calendar."],
                [MessageSquareText, "An easy return", "The customer can request help directly from the record."],
              ].map(([Icon, title, copy]) => {
                const FeatureIcon = Icon as typeof FileCheck2;
                return (
                  <article key={title as string} className="rounded-3xl border border-black/8 bg-white p-6 shadow-sm">
                    <FeatureIcon className="h-7 w-7 text-[#0b6575]" />
                    <h3 className="mt-5 text-xl font-semibold text-pns-text-primary">{title as string}</h3>
                    <p className="mt-3 leading-7 text-pns-text-muted">{copy as string}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </Container>
      </section>

      <section id="how-it-works" className="bg-white py-20 lg:py-24">
        <Container>
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">How it works</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
              Three small steps after every job.
            </h2>
            <p className="mt-5 text-lg leading-8 text-pns-text-muted">
              Your customer gets something useful today. Your business gets a better chance at tomorrow&apos;s work.
            </p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {workflow.map((step) => (
              <article key={step.number} className="rounded-3xl border border-black/10 bg-[#f7f9f9] p-7">
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#071729] text-cyan-300">
                    <step.icon className="h-6 w-6" />
                  </span>
                  <span className="text-sm font-semibold text-[#0b6575]">{step.number}</span>
                </div>
                <h3 className="mt-7 text-2xl font-semibold text-pns-text-primary">{step.title}</h3>
                <p className="mt-3 leading-7 text-pns-text-muted">{step.copy}</p>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="overflow-hidden bg-[#eaf4f4] py-20 lg:py-24">
        <Container>
          <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">What your customer sees</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
                A useful page with your business attached.
              </h2>
              <p className="mt-5 text-lg leading-8 text-pns-text-muted">
                Not another customer portal. Not another password. Just the important details and a clear way to reach the person who knows the work.
              </p>
              <ul className="mt-7 space-y-4">
                {["What was repaired or installed", "Warranty and care instructions", "Photos, model numbers, and receipts", "Recommended next service date", "A button to request another visit"].map((item) => (
                  <li key={item} className="flex gap-3 text-lg text-pns-text-primary">
                    <Check className="mt-1 h-5 w-5 shrink-0 text-[#0b6575]" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="mx-auto w-full max-w-2xl rounded-[2rem] bg-[#071729] p-3 shadow-2xl sm:p-5">
              <div className="overflow-hidden rounded-[1.4rem] bg-white">
                <div className="border-b border-black/8 bg-[#f7f9f9] px-6 py-5 sm:px-8">
                  <div className="flex items-start justify-between gap-5">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.12em] text-[#0b6575]">Your service record</p>
                      <h3 className="mt-2 text-2xl font-semibold text-pns-text-primary">Hot water tank service</h3>
                      <p className="mt-1 text-sm text-pns-text-muted">Completed August 18, 2026</p>
                    </div>
                    <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">Complete</span>
                  </div>
                </div>
                <div className="space-y-5 p-6 sm:p-8">
                  <div>
                    <p className="text-sm font-semibold text-pns-text-primary">What we did</p>
                    <p className="mt-2 leading-7 text-pns-text-muted">Inspected the tank, replaced the pressure valve, and confirmed normal operation.</p>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl bg-[#f2f6f6] p-4">
                      <p className="text-sm font-semibold text-pns-text-primary">Warranty</p>
                      <p className="mt-1 text-sm leading-6 text-pns-text-muted">Parts and labour covered until August 18, 2027</p>
                    </div>
                    <div className="rounded-2xl bg-[#f2f6f6] p-4">
                      <p className="text-sm font-semibold text-pns-text-primary">Recommended service</p>
                      <p className="mt-1 text-sm leading-6 text-pns-text-muted">February 18, 2027</p>
                    </div>
                  </div>
                  <button type="button" className="w-full rounded-xl bg-cyan-300 px-5 py-3 font-semibold text-[#071729]">
                    Ask for service
                  </button>
                  <p className="text-center text-xs text-pns-text-muted">Service provided by North Shore Mechanical</p>
                </div>
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-24">
        <Container>
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Made for work that needs service again</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
                If maintenance matters, being remembered matters.
              </h2>
              <p className="mt-5 text-lg leading-8 text-pns-text-muted">
                Never Forget is designed for small operators who stand behind their work and want repeat customers without a complicated CRM project.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {trades.map((trade) => (
                <div key={trade} className="flex items-center gap-3 rounded-2xl bg-[#f5f7f7] p-4 font-medium text-pns-text-primary">
                  <Check className="h-5 w-5 shrink-0 text-[#0b6575]" />
                  {trade}
                </div>
              ))}
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-[#f4f7f7] py-20">
        <Container>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              [LockKeyhole, "Private by design", "Each customer receives a private link. Their contact details are not shown on the public page."],
              [ShieldCheck, "The customer stays in control", "They can stop reminders whenever they want. No surprise marketing messages."],
              [CalendarCheck, "Useful reminders only", "The date comes from the work you completed, not a generic sales campaign."],
            ].map(([Icon, title, copy]) => {
              const TrustIcon = Icon as typeof LockKeyhole;
              return (
                <article key={title as string} className="rounded-3xl bg-white p-7">
                  <TrustIcon className="h-7 w-7 text-[#0b6575]" />
                  <h3 className="mt-5 text-xl font-semibold text-pns-text-primary">{title as string}</h3>
                  <p className="mt-3 leading-7 text-pns-text-muted">{copy as string}</p>
                </article>
              );
            })}
          </div>
        </Container>
      </section>

      <section className="bg-[#071729] py-20 text-white">
        <Container size="narrow">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">Never Forget contractor pilot</p>
            <h2 className="mt-4 text-4xl font-semibold tracking-tight lg:text-5xl">Do good work once. Make it easier to earn the next job.</h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-white/75">
              We are inviting a small group of Canadian service businesses to test the complete workflow and help shape the product.
            </p>
            <div className="mt-8">
              <Button href="/contact?product=never-forget" size="lg" className="bg-cyan-300 !text-[#071729] hover:bg-cyan-200">
                Join the pilot <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
            <p className="mt-4 text-sm text-white/55">No customer app. No customer login. No annual contract.</p>
          </div>
        </Container>
      </section>
    </main>
  );
}
