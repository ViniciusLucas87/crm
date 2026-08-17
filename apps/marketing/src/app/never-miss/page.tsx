import type { Metadata } from "next";
import Image from "next/image";
import { ArrowRight, Check, PhoneMissed } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "Never Miss | Automatic Missed Call Texts for Service Businesses",
  description: "We text missed callers right away and give you a simple callback list. Built for busy contractors and service businesses.",
  alternates: { canonical: "/never-miss" },
};

const goodFit = [
  "You work with your hands and cannot always pick up",
  "New customers usually call before they book",
  "You want a simple callback list, not another complicated app",
  "One saved job would easily pay for the service",
];

const workflow = [
  {
    image: "/images/never-miss-step-call.png",
    alt: "A plumber working under a sink while his phone rings nearby",
    number: "01",
    title: "A call goes unanswered",
    copy: "You keep working. We notice the missed call.",
  },
  {
    image: "/images/never-miss-step-text.png",
    alt: "A homeowner reading an automatic missed call reply on her phone",
    number: "02",
    title: "The customer gets a text",
    copy: "They know you got the call and can tell you what they need.",
  },
  {
    image: "/images/never-miss-step-callback.png",
    alt: "A contractor returning a customer call from his parked work van",
    number: "03",
    title: "You call them back",
    copy: "Their number and message are waiting when you are free.",
  },
];

const packages = [
  {
    name: "Never Miss",
    price: "$19.99",
    description: "For an owner who needs every missed caller to hear back quickly.",
    features: ["Automatic text after a missed call", "Custom reply message", "Callback reminders", "Missed call history"],
  },
  {
    name: "Never Miss Plus",
    price: "$59",
    description: "For a team that wants every new inquiry organized in one place.",
    features: ["Everything in Never Miss", "Replies collected in one inbox", "Website and form inquiries", "Contact status and next action", "Simple follow-up tracking"],
  },
];

export default function ProductsPage() {
  return (
    <main>
      <section className="relative min-h-[680px] overflow-hidden bg-[#071729] text-white">
        <Image
          src="/images/never-miss-contractor-hero.gif"
          alt="A service contractor checking a customer message while working"
          fill
          priority
          sizes="100vw"
          unoptimized
          className="object-cover object-[58%_center] lg:left-auto lg:right-0 lg:w-[68%] lg:object-center"
        />
        <div className="absolute inset-0 bg-[#071729]/40 lg:bg-gradient-to-r lg:from-[#071729] lg:from-[0%] lg:via-[#071729]/72 lg:via-[24%] lg:to-transparent lg:to-[48%]" />
        <Container className="relative flex min-h-[680px] items-center py-20">
          <div className="max-w-2xl lg:max-w-[46%]">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">For busy contractors and service owners</p>
            <h1 className="mt-5 text-[clamp(3rem,7vw,5.6rem)] font-semibold leading-[0.95] tracking-[-0.045em]">Can&apos;t answer? We text them back.</h1>
            <p className="mt-7 max-w-xl text-xl leading-8 text-white/85">You keep working. We let the caller know you will get back to them and put the job on your callback list.</p>
            <p className="mt-4 text-base font-semibold text-white">No new phone number. No complicated setup. No lost lead.</p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button href="/never-miss/checkout?plan=never-miss" size="lg" className="bg-cyan-300 !text-[#071729] hover:bg-cyan-200">Start Never Miss for $19.99/month <ArrowRight className="h-4 w-4" /></Button>
              <Button href="#how-it-works" variant="outline" size="lg" className="border-white/40 !text-white hover:bg-white/10">See what happens</Button>
            </div>
            <p className="mt-4 text-sm text-white/65">We set it up with you. Cancel anytime.</p>
          </div>
        </Container>
      </section>

      <section className="bg-[#f4f7f7] py-20 lg:py-24">
        <Container>
          <div className="mx-auto max-w-3xl text-center"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Choose what fits today</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">One product. Two simple packages.</h2><p className="mt-5 text-lg leading-8 text-pns-text-muted">Start with the missed call reply. Move to Plus when you want calls, texts, and website inquiries together.</p></div>
          <div className="mx-auto mt-12 grid max-w-5xl gap-6 lg:grid-cols-2">
            {packages.map((item, index) => (
              <article key={item.name} className={`rounded-3xl p-8 ${index === 1 ? "bg-[#071729] text-white" : "border border-black/10 bg-white text-pns-text-primary"}`}>
                <h3 className="text-3xl font-semibold">{item.name}</h3>
                <div className="mt-5 flex items-end gap-2"><span className="text-5xl font-semibold tracking-tight">{item.price}</span><span className={index === 1 ? "pb-1 text-white/60" : "pb-1 text-pns-text-muted"}>CAD/month</span></div>
                <p className={`mt-5 leading-7 ${index === 1 ? "text-white/72" : "text-pns-text-muted"}`}>{item.description}</p>
                <ul className="mt-7 space-y-3">{item.features.map((feature) => <li key={feature} className="flex gap-3"><Check className={`mt-0.5 h-5 w-5 shrink-0 ${index === 1 ? "text-cyan-300" : "text-[#0b6575]"}`} />{feature}</li>)}</ul>
                <div className="mt-8"><Button href={`/never-miss/checkout?plan=${index === 1 ? "never-miss-plus" : "never-miss"}`} size="lg" className={index === 1 ? "bg-cyan-300 !text-[#071729] hover:bg-cyan-200" : undefined}>Start {item.name} <ArrowRight className="h-4 w-4" /></Button></div>
                <p className={`mt-3 text-sm ${index === 1 ? "text-white/55" : "text-pns-text-muted"}`}>Cancel anytime.</p>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section id="how-it-works" className="bg-white py-20 lg:py-24">
        <Container>
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">What happens when you miss a call</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">Your customer hears back before they call the next company.</h2>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {workflow.map((step) => (
              <article key={step.number} className="overflow-hidden rounded-3xl border border-black/10 bg-white">
                <div className="relative aspect-[4/3] overflow-hidden">
                  <Image src={step.image} alt={step.alt} fill sizes="(min-width: 768px) 33vw, 100vw" className="object-cover" />
                </div>
                <div className="p-7">
                  <p className="text-sm font-semibold text-[#0b6575]">{step.number}</p>
                  <h3 className="mt-2 text-2xl font-semibold text-pns-text-primary">{step.title}</h3>
                  <p className="mt-3 leading-7 text-pns-text-muted">{step.copy}</p>
                </div>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="bg-[#edf5f5] py-20 lg:py-24">
        <Container>
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">A real example</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">A homeowner calls while you are working.</h2>
              <p className="mt-5 text-lg leading-8 text-pns-text-muted">You cannot answer. Instead of hearing nothing, they receive a text from your company. They reply with what they need. When you are free, you already know who to call and why.</p>
            </div>
            <div className="rounded-[2rem] bg-[#071729] p-6 text-white shadow-xl sm:p-9">
              <div className="flex items-center gap-3 border-b border-white/15 pb-5"><PhoneMissed className="h-7 w-7 text-cyan-300" /><div><p className="font-semibold">Missed call from (604) 555 0142</p><p className="text-sm text-white/55">Today at 10:42 AM</p></div></div>
              <div className="my-5 ml-auto max-w-[92%] rounded-2xl rounded-tr-sm bg-cyan-300 p-4 text-base leading-7 text-[#071729]">Hi, this is North Shore Plumbing. Sorry we missed your call. Reply here with your name and what you need. We will call you back shortly.</div>
              <div className="max-w-[82%] rounded-2xl rounded-tl-sm bg-white/12 p-4 text-base leading-7">Hi, it&apos;s Mike. Our kitchen sink is leaking. We are in North Vancouver.</div>
              <p className="mt-6 text-sm font-semibold text-cyan-300">Callback added to your list</p>
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-24">
        <Container>
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Is this for you?</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">Built for small teams that win work by phone.</h2><p className="mt-5 text-lg leading-8 text-pns-text-muted">Plumbers, electricians, cleaners, landscapers, contractors, repair shops, mobile services, and other owners who cannot stop working every time the phone rings.</p></div>
            <ul className="space-y-4">{goodFit.map((item) => <li key={item} className="flex gap-3 rounded-2xl bg-[#f5f7f7] p-4 text-lg text-pns-text-primary"><Check className="mt-1 h-5 w-5 shrink-0 text-[#0b6575]" />{item}</li>)}</ul>
          </div>
        </Container>
      </section>

      <section className="bg-[#071729] py-20 text-white">
        <Container size="narrow">
          <div className="text-center"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">Never Miss</p><h2 className="mt-4 text-4xl font-semibold tracking-tight lg:text-5xl">Start for CAD $19.99 per month.</h2><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-white/75">We connect your phone, write the message with you, and test a real missed call. See how many customers it saves.</p><div className="mt-8"><Button href="/never-miss/checkout?plan=never-miss" size="lg" className="bg-cyan-300 !text-[#071729] hover:bg-cyan-200">Start Never Miss <ArrowRight className="h-4 w-4" /></Button></div><p className="mt-4 text-sm text-white/55">Cancel anytime. No annual contract. No software training required.</p></div>
        </Container>
      </section>
    </main>
  );
}
