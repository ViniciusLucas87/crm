"use client";

import { ComponentPropsWithoutRef, FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { CheckCircle2, LoaderCircle, PhoneCall } from "lucide-react";
import { Container } from "@/components/ui/container";

const API = "";

type Setup = {
  plan: "never_miss" | "never_miss_plus";
  status: string;
  customer_name?: string;
  business_name?: string;
  notification_phone?: string;
  assigned_phone?: string;
};

type Activated = {
  status: "active";
  plan: string;
  assigned_phone: string;
  forward_from?: string;
  next_step?: string;
  management_token?: string;
};

export default function NeverMissActivatePage() {
  return <Suspense fallback={<main className="min-h-screen bg-[#f4f7f7] p-12 text-[#071729]">Confirming your subscription…</main>}><ActivationForm /></Suspense>;
}

function ActivationForm() {
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("token") || "");
  const [setup, setSetup] = useState<Setup | null>(null);
  const [activated, setActivated] = useState<Activated | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  const [confirmationMessage, setConfirmationMessage] = useState("Trial confirmed. Preparing your secure setup…");

  useEffect(() => {
    let cancelled = false;
    async function begin() {
      try {
        let activationToken = token;
        const checkoutSession = params.get("session_id");
        if (!activationToken && checkoutSession) {
          let exchanged: Response | null = null;
          for (let attempt = 0; attempt < 40; attempt += 1) {
            exchanged = await fetch(`${API}/api/v1/subscriptions/onboarding/exchange`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ checkout_session_id: checkoutSession }),
            });
            if (exchanged.status !== 409) break;
            if (!cancelled && attempt >= 3) {
              setConfirmationMessage("Stripe confirmed your trial. It is securely connecting your setup. This usually takes less than a minute…");
            }
            await new Promise((resolve) => setTimeout(resolve, 1500));
          }
          if (!exchanged) throw new Error("Your payment is safe, but setup could not start automatically. Refresh this page or use the private link in your email.");
          if (!exchanged.ok) throw new Error("Your payment is safe. Setup is taking longer than expected. Refresh this page or use the private link in your email.");
          const result = await exchanged.json();
          if (result.status === "active") {
            if (!cancelled) setActivated(result);
            return;
          }
          activationToken = result.token;
          if (!cancelled) setToken(activationToken);
        }
        if (!activationToken) throw new Error("This page needs the private activation link sent after payment.");
        const response = await fetch(`${API}/api/v1/subscriptions/onboarding/${encodeURIComponent(activationToken)}`, { cache: "no-store" });
        if (!response.ok) throw new Error(response.status === 410 ? "This activation link expired. Contact us for a new link." : "This activation link is invalid.");
        const result = await response.json();
        if (!cancelled) {
          setSetup(result);
          if (result.status === "active") setActivated(result);
        }
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Setup could not be loaded.");
      } finally {
        if (!cancelled) setBusy(false);
      }
    }
    begin();
    return () => { cancelled = true; };
  }, [params, token]);

  async function activate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const values = new FormData(event.currentTarget);
    const payload = {
      business_name: values.get("business_name"),
      contact_name: values.get("contact_name"),
      notification_phone: values.get("notification_phone"),
      existing_business_phone: values.get("existing_business_phone"),
      preferred_area_code: values.get("preferred_area_code"),
      recovery_message: values.get("recovery_message"),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "America/Vancouver",
      website_url: setup?.plan === "never_miss_plus" ? values.get("website_url") || null : null,
      consent_to_text_callers: values.get("consent_to_text_callers") === "on",
      accept_terms: values.get("accept_terms") === "on",
    };
    try {
      const response = await fetch(`${API}/api/v1/subscriptions/onboarding/${encodeURIComponent(token)}/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Activation did not finish. Your answers are saved, so it is safe to retry.");
      setActivated(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Activation did not finish.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f7f7] py-12 lg:py-20">
      <Container size="narrow">
        <div className="mx-auto max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Never Miss setup</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-[#071729] lg:text-5xl">Connect your phone in a few minutes.</h1>
          <p className="mt-4 text-lg text-slate-600">Your trial is confirmed. Tell us how your business should answer missed calls and we will prepare the service automatically.</p>

          {busy && !setup && !activated ? <div className="mt-10 flex items-center gap-3 rounded-2xl border border-emerald-100 bg-white p-6 text-[#071729] shadow"><LoaderCircle className="h-5 w-5 animate-spin text-emerald-600" /><div><p className="font-semibold">{confirmationMessage}</p><p className="mt-1 text-sm text-slate-500">Please keep this page open. You will not be charged again.</p></div></div> : null}
          {error ? <div className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800">{error}</div> : null}

          {activated ? (
            <section className="mt-10 rounded-3xl bg-[#071729] p-8 text-white shadow-xl">
              <CheckCircle2 className="h-12 w-12 text-cyan-300" />
              <h2 className="mt-5 text-3xl font-semibold">Your current business number stays the same.</h2>
              <p className="mt-4 text-lg text-white/75">Private Never Miss routing line</p>
              <p className="mt-1 text-4xl font-semibold tracking-tight">{activated.assigned_phone}</p>
              <p className="mt-3 text-sm text-white/60">Do not advertise this number. Customers continue calling {activated.forward_from || "your existing business number"}.</p>
              <div className="mt-7 rounded-2xl bg-white/10 p-5">
                <p className="font-semibold">Connect unanswered calls only</p>
                <ol className="mt-3 space-y-2 text-white/75"><li>1. Choose the instructions below that match your phone.</li><li>2. Select only <strong>When unanswered</strong>, <strong>No answer</strong>, or <strong>No reply</strong>, then enter the private routing line above.</li><li>3. From another phone, first answer one call to confirm it stays on your normal number. Then place a second call, do not answer, and wait for the automatic text.</li></ol>
                <p className="mt-4 text-sm text-white/60">Do not select Always forward, Forward all calls, Busy, or Unreachable. Answered calls must continue working normally.</p>
              </div>

              <div className="mt-8">
                <p className="text-sm font-semibold uppercase tracking-[0.14em] text-cyan-300">Simple phone setup</p>
                <h3 className="mt-2 text-2xl font-semibold">Choose “When unanswered”, not “Forward all calls”.</h3>
                <p className="mt-3 text-white/70">Phone menus vary. The examples show the one setting Never Miss needs. If your carrier uses different words, ask for conditional forwarding when there is no answer.</p>
                <div className="mt-6 overflow-hidden rounded-2xl bg-white p-3">
                  <Image src="/images/never-miss-setup/unanswered-calls-only.svg" alt="A business phone rings first and only an unanswered call goes to the private Never Miss routing line. Always forward, busy, and unreachable forwarding are not selected." width={1200} height={720} sizes="(min-width: 768px) 720px, 100vw" className="h-auto w-full" />
                </div>
                <div className="mt-6 grid gap-5 md:grid-cols-3">
                  <SetupOption image="/images/never-miss-setup/iphone-forwarding-example.png" title="iPhone" steps={["Open Settings, Apps, then Phone.", "Look for Call Forwarding or contact your carrier.", "Choose When Unanswered only, enter the private routing line, and leave every other forwarding condition off."]} />
                  <SetupOption image="/images/never-miss-setup/android-forwarding-example.png" title="Android" steps={["Open the Phone app and its Settings menu.", "Open Calling accounts or Supplementary services.", "Choose Call forwarding, then When unanswered only. Do not enable Always forward, Busy, or Unreachable."]} />
                  <SetupOption image="/images/never-miss-setup/dial-code-example.png" title="Carrier code" steps={[`A common unanswered-call code is *61*${activated.assigned_phone.replace(/\D/g, "")}#`, "Press Call and wait for confirmation.", "Do not use an all-calls code. Codes vary, so confirm the no-answer code with your carrier if this is rejected."]} />
                </div>
              </div>

              <div className="mt-8 rounded-2xl border border-amber-200/25 bg-amber-100/10 p-5">
                <p className="font-semibold text-amber-100">Before changing voicemail</p>
                <p className="mt-2 text-sm leading-6 text-white/75">On many phone plans, forwarding unanswered calls replaces the route that normally sends callers to carrier voicemail. Your saved messages should remain, but new unanswered callers may go to Never Miss instead of voicemail. If voicemail is essential to your business, confirm the behaviour with your carrier before changing it.</p>
              </div>

              <div className="mt-5 rounded-2xl bg-cyan-300/10 p-5">
                <p className="font-semibold text-cyan-200">What to expect during the test</p>
                <p className="mt-2 text-sm leading-6 text-white/75">Let the call ring until it forwards, then hang up. The text normally arrives within about 10 to 25 seconds. Carrier and mobile network conditions can sometimes add a little more time.</p>
              </div>
              {activated.management_token ? <Link href={`/never-miss/manage#token=${encodeURIComponent(activated.management_token)}`} className="mt-6 flex min-h-14 items-center justify-center rounded-xl bg-cyan-300 px-6 py-3 text-lg font-semibold text-[#071729] hover:bg-cyan-200">Manage my Never Miss service</Link> : null}
            </section>
          ) : setup ? (
            <form onSubmit={activate} className="mt-10 space-y-6 rounded-3xl bg-white p-7 shadow-xl sm:p-9">
              <div className="rounded-2xl bg-[#edf5f5] p-5"><p className="font-semibold text-[#071729]">Your plan: {setup.plan === "never_miss_plus" ? "Never Miss Plus" : "Never Miss"}</p><p className="mt-1 text-sm text-slate-600">Keep your existing business number. A private routing line handles only unanswered calls.</p></div>
              <Field label="Business name" name="business_name" defaultValue={setup.business_name} required />
              <Field label="Your name" name="contact_name" defaultValue={setup.customer_name} required />
              <Field label="Business phone customers call today" name="existing_business_phone" type="tel" placeholder="+1 604 555 0123" required />
              <Field label="Mobile number for callback alerts" name="notification_phone" type="tel" defaultValue={setup.notification_phone} placeholder="+1 604 555 0123" required />
              <Field label="Preferred Canadian area code" name="preferred_area_code" inputMode="numeric" pattern="[0-9]{3}" placeholder="604" required />
              {setup.plan === "never_miss_plus" ? <Field label="Website" name="website_url" type="url" placeholder="https://yourbusiness.ca" /> : null}
              <label className="block"><span className="font-semibold text-[#071729]">Automatic reply message</span><textarea name="recovery_message" required minLength={20} maxLength={500} defaultValue={`Hi, this is ${setup.business_name || "our team"}. Sorry we missed your call. Reply with your name and what you need, and we will call you back shortly. Reply STOP to opt out.`} className="mt-2 min-h-32 w-full rounded-xl border border-slate-300 px-4 py-3 text-[#071729] outline-none focus:border-[#0b6575]" /></label>
              <label className="flex gap-3 text-sm text-slate-700"><input type="checkbox" name="consent_to_text_callers" required className="mt-1" /><span>I confirm that this message identifies my business, contains opt out instructions, and will only be sent in response to an eligible call.</span></label>
              <label className="flex gap-3 text-sm text-slate-700"><input type="checkbox" name="accept_terms" required className="mt-1" /><span>I accept the <Link className="underline" href="/terms" target="_blank">service terms</Link>, <Link className="underline" href="/privacy" target="_blank">privacy policy</Link>, and <Link className="underline" href="/acceptable-use" target="_blank">acceptable-use rules</Link>, and authorize Pacific North Systems to provision the phone number included in my plan.</span></label>
              <button disabled={busy} className="flex min-h-14 w-full items-center justify-center gap-2 rounded-xl bg-[#071729] px-6 py-3 text-lg font-semibold text-white hover:bg-[#0b6575] disabled:opacity-60"><PhoneCall className="h-5 w-5" />{busy ? "Activating…" : "Activate Never Miss"}</button>
              <p className="text-center text-sm text-slate-500">No staff appointment is required. We will never ask for your carrier password. Need help? <a className="underline" href="mailto:hello@pacificnorthsystems.com?subject=Never%20Miss%20setup%20help">Email us</a>.</p>
            </form>
          ) : null}
        </div>
      </Container>
    </main>
  );
}

function SetupOption({ image, title, steps }: { image: string; title: string; steps: string[] }) {
  return (
    <article className="overflow-hidden rounded-2xl bg-white text-[#071729]">
      <div className="relative aspect-[4/5] bg-slate-100">
        <Image src={image} alt={`${title} example for forwarding unanswered calls`} fill sizes="(min-width: 768px) 220px, 100vw" className="object-cover" />
      </div>
      <div className="p-5">
        <h4 className="text-lg font-semibold">{title}</h4>
        <ol className="mt-3 space-y-2 text-sm leading-5 text-slate-600">{steps.map((step, index) => <li key={step}><span className="font-semibold text-[#0b6575]">{index + 1}.</span> {step}</li>)}</ol>
      </div>
    </article>
  );
}

function Field({ label, name, ...props }: { label: string; name: string } & Omit<ComponentPropsWithoutRef<"input">, "name">) {
  return <label className="block"><span className="font-semibold text-[#071729]">{label}</span><input name={name} {...props} className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 py-3 text-[#071729] outline-none focus:border-[#0b6575]" /></label>;
}
