import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Check, PhoneMissed, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { TrialCta } from "@/components/never-miss/trial-cta";
import { siteConfig } from "@/lib/site-config";

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
    plan: "never-miss" as const,
    name: "Never Miss",
    price: "$39",
    trial: "30 days free, then $39 CAD/month",
    description: "For an owner who needs every missed caller to hear back quickly.",
    features: ["Automatic text after an eligible unanswered call", "Custom reply message", "Callback reminders and missed-call history", "Up to 50 calls and 100 recovery messages each month"],
  },
  {
    plan: "never-miss-plus" as const,
    name: "Never Miss Plus",
    price: "$89",
    trial: "30 days free, then $89 CAD/month",
    description: "For a team that needs higher capacity and one place to review more customer inquiries.",
    features: ["Everything in Never Miss", "One inbox for calls, texts, forms, and website inquiries", "Simple follow-up tracking", "Up to 250 calls and 500 recovery messages each month"],
  },
];

const checkoutAvailable = Boolean(
  process.env.NEVER_MISS_FREE_TRIAL_URL || process.env.NEVER_MISS_CHECKOUT_URL,
);

export default function ProductsPage() {
  return (
    <main>
      <section className="relative overflow-hidden bg-[#071729] text-white lg:min-h-[680px]">
        <div className="pointer-events-none absolute inset-0 z-[1] hidden bg-gradient-to-r from-[#071729] from-[0%] via-[#071729] via-[44%] to-transparent to-[52%] lg:block" />
        <Container className="relative z-10 flex items-center py-14 sm:py-16 lg:min-h-[680px] lg:py-20">
          <div className="max-w-2xl lg:max-w-[38%]">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">For busy contractors and service owners</p>
            <h1 className="mt-5 text-[clamp(2.75rem,12vw,5.2rem)] font-semibold leading-[0.95] tracking-[-0.045em] lg:text-[clamp(3rem,5vw,5.2rem)]">Can&apos;t answer? We text them back.</h1>
            <p className="mt-7 max-w-xl text-xl leading-8 text-white/85">You keep working. We let the caller know you will get back to them and put the job on your callback list.</p>
            <p className="mt-4 text-base font-semibold text-white">No new phone number. No complicated setup. No lost lead.</p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <TrialCta available={checkoutAvailable} label={checkoutAvailable ? "Start your 30-day free test" : "Talk to our team"} className="w-full bg-cyan-300 !text-[#071729] hover:bg-cyan-200 sm:w-auto" />
              <Button href="#how-it-works" variant="outline" size="lg" className="w-full border-white/40 !text-white hover:bg-white/10 sm:w-auto">See what happens</Button>
            </div>
            <p className="mt-4 text-sm text-white/65">{checkoutAvailable ? "No charge today. Your subscription continues monthly after 30 days unless you cancel beforehand." : "Online trial enrolment is temporarily unavailable. We will not take payment until the self-service checkout is ready."}</p>
          </div>
        </Container>
        <div className="relative h-[420px] w-full sm:h-[500px] lg:absolute lg:inset-y-0 lg:left-[48%] lg:h-auto lg:w-[52%]">
          <Image
            src="/images/never-miss-contractor-hero.gif"
            alt="A service contractor checking a customer message while working"
            fill
            priority
            sizes="(min-width: 1024px) 52vw, 100vw"
            unoptimized
            className="object-cover object-[58%_center] lg:object-[center_35%]"
          />
        </div>
      </section>

      <section className="bg-[#071729] py-20 text-white lg:py-24">
        <Container>
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">See Never Miss in action</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight lg:text-5xl">One missed call. One automatic reply. One clear callback.</h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-white/75">Watch how Never Miss protects the next job while you keep working.</p>
          </div>
          <div className="mx-auto mt-10 max-w-5xl overflow-hidden rounded-3xl border border-white/15 bg-black shadow-2xl">
            <video className="aspect-video w-full" controls playsInline preload="metadata">
              <source src="/videos/never-miss-product-demo.mp4" type="video/mp4" />
              <track src="/videos/never-miss-product-demo.en.vtt" kind="captions" srcLang="en" label="English" />
              Your browser does not support video playback.
            </video>
          </div>
        </Container>
      </section>

      <section className="bg-[#f4f7f7] py-20 lg:py-24">
        <Container>
          <div className="mx-auto max-w-3xl text-center"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Simple, focused service</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">One clear missed-call workflow.</h2><p className="mt-5 text-lg leading-8 text-pns-text-muted">Never Miss is focused on helping you acknowledge unanswered callers and organize the callback.</p></div>
          <div className="mx-auto mt-12 grid max-w-5xl gap-6 lg:grid-cols-2">
            {packages.map((item, index) => (
              <article key={item.name} className={`rounded-3xl p-8 ${index === 1 ? "bg-[#071729] text-white" : "border border-black/10 bg-white text-pns-text-primary"}`}>
                <h3 className="text-3xl font-semibold">{item.name}</h3>
                <div className="mt-5"><p className="text-2xl font-semibold tracking-tight">30 days free</p><p className={index === 1 ? "mt-1 text-white/60" : "mt-1 text-pns-text-muted"}>Then {item.price} CAD/month</p></div>
                <p className={`mt-5 leading-7 ${index === 1 ? "text-white/72" : "text-pns-text-muted"}`}>{item.description}</p>
                <ul className="mt-7 space-y-3">{item.features.map((feature) => <li key={feature} className="flex gap-3"><Check className={`mt-0.5 h-5 w-5 shrink-0 ${index === 1 ? "text-cyan-300" : "text-[#0b6575]"}`} />{feature}</li>)}</ul>
                <div className="mt-8"><TrialCta plan={item.plan} available={checkoutAvailable} label={checkoutAvailable ? "Start free test" : "Contact us"} /></div>
                <p className="mt-3 text-sm text-pns-text-muted">{checkoutAvailable ? `${item.trial}. Cancel anytime.` : "Online trials are not open until checkout verification is complete."}</p>
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
          <div className="mx-auto max-w-3xl text-center"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Only after you do not answer</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">Your team gets the first chance to answer.</h2><p className="mt-5 text-lg leading-8 text-pns-text-muted">Never Miss is not all-calls forwarding and does not replace your staff. Your carrier forwards an eligible call only when it goes unanswered. Answered calls continue through your normal business number.</p></div>
          <div className="mx-auto mt-12 grid max-w-5xl gap-5 md:grid-cols-3">
            {["A customer calls the number you already advertise.", "Your team answers as normal. Nothing changes.", "If the call is unanswered, your approved reply and callback workflow begin."].map((item, index) => <div key={item} className="rounded-2xl bg-white p-6 shadow-sm"><p className="text-sm font-semibold text-[#0b6575]">0{index + 1}</p><p className="mt-3 text-lg leading-7 text-pns-text-primary">{item}</p></div>)}
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-24">
        <Container>
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">A trial that is tested, not assumed</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">Set up unanswered-call forwarding, then test a real call.</h2><p className="mt-5 text-lg leading-8 text-pns-text-muted">After secure checkout, you choose the reply, confirm the business number and notification number, and receive a private routing line. Set your carrier to forward <strong>when unanswered only</strong>. Then test from another phone before relying on it with customers.</p></div>
            <ol className="space-y-4">{["Start the 30-day free trial. A card is collected, but there is no charge today.", "Complete the short setup and confirm your customer reply includes clear opt-out wording.", "Use your carrier's no-answer or when-unanswered forwarding option only. Do not enable all-calls forwarding.", "Place one answered test call, then one unanswered test call. Confirm the text, customer response, callback task, and notification."].map((item, index) => <li key={item} className="flex gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-5"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#071729] text-sm font-semibold text-cyan-200">{index + 1}</span><span className="leading-7 text-pns-text-primary">{item}</span></li>)}</ol>
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

      <section className="bg-[#edf5f5] py-20 lg:py-24">
        <Container size="narrow">
          <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm sm:p-10"><div className="flex items-center gap-3"><ShieldCheck className="h-7 w-7 text-[#0b6575]" /><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Clear terms and support</p></div><h2 className="mt-4 text-3xl font-semibold tracking-tight text-pns-text-primary">Know what happens before you start.</h2><div className="mt-6 grid gap-5 md:grid-cols-2"><p className="leading-7 text-pns-text-muted"><strong className="text-pns-text-primary">Billing:</strong> Never Miss is free for 30 days, then $39 CAD/month. Never Miss Plus is free for 30 days, then $89 CAD/month. Cancel before the trial ends to avoid the first monthly charge.</p><p className="leading-7 text-pns-text-muted"><strong className="text-pns-text-primary">Messages:</strong> You approve the reply during setup and confirm that it identifies your business, includes opt-out wording, and is used only after eligible unanswered calls.</p><p className="leading-7 text-pns-text-muted"><strong className="text-pns-text-primary">Cancellation:</strong> You can cancel anytime. If service ends, remove unanswered-call forwarding so callers return to your normal voicemail process.</p><p className="leading-7 text-pns-text-muted"><strong className="text-pns-text-primary">Support:</strong> Need help with setup or a payment question? Email <a className="text-[#0b6575] underline" href={`mailto:${siteConfig.contact.email}`}>{siteConfig.contact.email}</a>. We aim to respond within one business day.</p></div><div className="mt-8 flex flex-wrap gap-x-5 gap-y-3 text-sm font-semibold text-[#0b6575]"><Link href="/privacy" className="hover:underline">Privacy policy</Link><Link href="/terms" className="hover:underline">Terms of service</Link><Link href="/acceptable-use" className="hover:underline">Acceptable use</Link><Link href="/never-miss/manage" className="hover:underline">Manage an existing subscription</Link></div></div>
        </Container>
      </section>

      <section className="bg-[#071729] py-20 text-white">
        <Container size="narrow">
          <div className="text-center"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">Never Miss</p><h2 className="mt-4 text-4xl font-semibold tracking-tight lg:text-5xl">Keep your number. Never lose track of the callback.</h2><p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-white/75">Customers keep calling the number they already know. We connect unanswered calls, send your reply, and help you test the complete workflow.</p><div className="mt-8"><TrialCta available={checkoutAvailable} label={checkoutAvailable ? "Start your free test" : "Contact us"} className="bg-cyan-300 !text-[#071729] hover:bg-cyan-200" /></div><p className="mt-4 text-sm text-white/55">{checkoutAvailable ? "Cancel anytime. No annual contract. No software training required." : "We will open online trials only after checkout and phone delivery are verified."}</p></div>
        </Container>
      </section>
    </main>
  );
}
