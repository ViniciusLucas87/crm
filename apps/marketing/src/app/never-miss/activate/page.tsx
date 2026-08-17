"use client";

import { ComponentPropsWithoutRef, FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
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
  const [confirmationMessage, setConfirmationMessage] = useState("Payment received. Preparing your secure setup…");

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
              setConfirmationMessage("Payment confirmed. Stripe is securely connecting your setup. This usually takes less than a minute…");
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
          <p className="mt-4 text-lg text-slate-600">Your payment is confirmed. Tell us how your business should answer missed calls and we will prepare the service automatically.</p>

          {busy && !setup && !activated ? <div className="mt-10 flex items-center gap-3 rounded-2xl border border-emerald-100 bg-white p-6 text-[#071729] shadow"><LoaderCircle className="h-5 w-5 animate-spin text-emerald-600" /><div><p className="font-semibold">{confirmationMessage}</p><p className="mt-1 text-sm text-slate-500">Please keep this page open. You will not be charged again.</p></div></div> : null}
          {error ? <div className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800">{error}</div> : null}

          {activated ? (
            <section className="mt-10 rounded-3xl bg-[#071729] p-8 text-white shadow-xl">
              <CheckCircle2 className="h-12 w-12 text-cyan-300" />
              <h2 className="mt-5 text-3xl font-semibold">Your Never Miss number is ready.</h2>
              <p className="mt-4 text-lg text-white/75">New service number</p>
              <p className="mt-1 text-4xl font-semibold tracking-tight">{activated.assigned_phone}</p>
              <div className="mt-7 rounded-2xl bg-white/10 p-5">
                <p className="font-semibold">One last self service step</p>
                <p className="mt-2 text-white/75">Set unanswered call forwarding on your business phone to the number above. Then call your business, let it ring without answering, and confirm that the automatic text arrives.</p>
              </div>
            </section>
          ) : setup ? (
            <form onSubmit={activate} className="mt-10 space-y-6 rounded-3xl bg-white p-7 shadow-xl sm:p-9">
              <div className="rounded-2xl bg-[#edf5f5] p-5"><p className="font-semibold text-[#071729]">Your plan: {setup.plan === "never_miss_plus" ? "Never Miss Plus" : "Never Miss"}</p><p className="mt-1 text-sm text-slate-600">Includes one local Canadian service number.</p></div>
              <Field label="Business name" name="business_name" defaultValue={setup.business_name} required />
              <Field label="Your name" name="contact_name" defaultValue={setup.customer_name} required />
              <Field label="Business phone customers call today" name="existing_business_phone" type="tel" placeholder="+1 604 555 0123" required />
              <Field label="Mobile number for callback alerts" name="notification_phone" type="tel" defaultValue={setup.notification_phone} placeholder="+1 604 555 0123" required />
              <Field label="Preferred Canadian area code" name="preferred_area_code" inputMode="numeric" pattern="[0-9]{3}" placeholder="604" required />
              {setup.plan === "never_miss_plus" ? <Field label="Website" name="website_url" type="url" placeholder="https://yourbusiness.ca" /> : null}
              <label className="block"><span className="font-semibold text-[#071729]">Automatic reply message</span><textarea name="recovery_message" required minLength={20} maxLength={500} defaultValue={`Hi, this is ${setup.business_name || "our team"}. Sorry we missed your call. Reply with your name and what you need, and we will call you back shortly. Reply STOP to opt out.`} className="mt-2 min-h-32 w-full rounded-xl border border-slate-300 px-4 py-3 text-[#071729] outline-none focus:border-[#0b6575]" /></label>
              <label className="flex gap-3 text-sm text-slate-700"><input type="checkbox" name="consent_to_text_callers" required className="mt-1" /><span>I confirm that this message identifies my business, contains opt out instructions, and will only be sent in response to an eligible call.</span></label>
              <label className="flex gap-3 text-sm text-slate-700"><input type="checkbox" name="accept_terms" required className="mt-1" /><span>I accept the service terms and authorize Pacific North Systems to provision the phone number included in my plan.</span></label>
              <button disabled={busy} className="flex min-h-14 w-full items-center justify-center gap-2 rounded-xl bg-[#071729] px-6 py-3 text-lg font-semibold text-white hover:bg-[#0b6575] disabled:opacity-60"><PhoneCall className="h-5 w-5" />{busy ? "Activating…" : "Activate Never Miss"}</button>
              <p className="text-center text-sm text-slate-500">No staff appointment is required. We will never ask for your carrier password.</p>
            </form>
          ) : null}
        </div>
      </Container>
    </main>
  );
}

function Field({ label, name, ...props }: { label: string; name: string } & Omit<ComponentPropsWithoutRef<"input">, "name">) {
  return <label className="block"><span className="font-semibold text-[#071729]">{label}</span><input name={name} {...props} className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 py-3 text-[#071729] outline-none focus:border-[#0b6575]" /></label>;
}
