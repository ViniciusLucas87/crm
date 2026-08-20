"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, CreditCard, Headphones, LoaderCircle, PauseCircle, Save } from "lucide-react";
import { Container } from "@/components/ui/container";

type Account = {
  plan: string;
  status: string;
  business_name?: string;
  customer_email: string;
  assigned_phone?: string;
  existing_business_phone?: string;
  notification_phone?: string;
  recovery_message?: string;
  enabled: boolean;
  timezone?: string;
  website_url?: string;
  billing_portal_available: boolean;
  support_email: string;
  calls_this_month: number;
  messages_this_month: number;
  monthly_call_limit: number;
  monthly_message_limit: number;
  last_call_at?: string;
  setup_ready: boolean;
  trial_ends_at?: string | null;
  current_period_ends_at?: string | null;
  cancel_at_period_end: boolean;
  recovery_test?: { verified_at: string; call_public_uuid: string } | null;
  recent_recovery_tests: Array<{ call_public_uuid: string; detected_at: string; sms_sent_at?: string; callback_task_created: boolean }>;
};

export default function NeverMissManagePage() {
  return <Suspense fallback={<Loading />}><Manager /></Suspense>;
}

function Loading() {
  return <main className="min-h-screen bg-[#f4f7f7] p-12 text-[#071729]"><LoaderCircle className="mr-2 inline h-5 w-5 animate-spin" />Opening your account...</main>;
}

function Manager() {
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("token") || "");
  const [account, setAccount] = useState<Account | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(Boolean(token));

  useEffect(() => {
    if (!token && typeof window !== "undefined") {
      const fragment = new URLSearchParams(window.location.hash.replace(/^#/, ""));
      const fragmentToken = fragment.get("token") || "";
      if (fragmentToken) {
        setToken(fragmentToken);
        window.history.replaceState({}, "", "/never-miss/manage");
      }
      return;
    }
    if (!token) return;
    fetch("/api/v1/subscriptions/manage/session", {
      method: "POST",
      headers: { "X-Never-Miss-Token": token },
      cache: "no-store",
    })
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.detail || "Your secure link could not be opened.");
        setAccount(body);
      })
      .catch(reason => setError(reason instanceof Error ? reason.message : "Your secure link could not be opened."))
      .finally(() => setBusy(false));
  }, [token]);

  async function requestLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const email = String(new FormData(event.currentTarget).get("email") || "");
    try {
      const response = await fetch("/api/v1/subscriptions/manage/request-link", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }),
      });
      if (!response.ok) throw new Error("We could not send the account link. Please try again.");
      setMessage("Check your email. Your private account link is on its way.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "We could not send the account link.");
    } finally { setBusy(false); }
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    const values = new FormData(event.currentTarget);
    try {
      const response = await fetch("/api/v1/subscriptions/manage/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json", "X-Never-Miss-Token": token },
        body: JSON.stringify({
          notification_phone: values.get("notification_phone"),
          existing_business_phone: values.get("existing_business_phone"),
          recovery_message: values.get("recovery_message"),
          website_url: values.get("website_url"),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || account?.timezone,
          enabled: values.get("enabled") === "on",
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Your changes could not be saved.");
      setAccount(body);
      setMessage("Your Never Miss settings are saved.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Your changes could not be saved.");
    } finally { setBusy(false); }
  }

  async function confirmRecoveryTest(callPublicUuid: string) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/v1/subscriptions/manage/verify-recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Never-Miss-Token": token },
        body: JSON.stringify({
          call_public_uuid: callPublicUuid,
          confirmed_recovery_text_received: true,
          confirmed_callback_task_visible: true,
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "The recovery test could not be confirmed.");
      setAccount(body);
      setMessage("Your end-to-end recovery test is recorded.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The recovery test could not be confirmed.");
    } finally { setBusy(false); }
  }

  async function openBillingPortal() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/v1/subscriptions/manage/billing-portal", {
        method: "POST",
        headers: { "X-Never-Miss-Token": token },
      });
      const body = await response.json();
      if (!response.ok || !body.url) throw new Error(body.detail || "Billing self-service could not be opened.");
      window.location.assign(body.url);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Billing self-service could not be opened.");
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f7f7] py-12 text-[#071729] lg:py-20">
      <Container size="narrow">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Never Miss account</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight lg:text-5xl">Your service, in one place.</h1>
        <p className="mt-4 text-lg text-slate-600">Change how missed calls are handled, pause replies, or manage billing whenever you need.</p>
        {error ? <div className="mt-7 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800">{error}</div> : null}
        {message ? <div className="mt-7 flex gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-800"><CheckCircle2 className="h-5 w-5" />{message}</div> : null}
        {busy && !account ? <Loading /> : null}
        {(!token || (error && !account)) ? (
          <form onSubmit={requestLink} className="mt-10 rounded-3xl bg-white p-7 shadow-xl">
            <h2 className="text-2xl font-semibold">{error ? "Get a fresh account link" : "Email me a secure account link"}</h2>
            <p className="mt-2 text-slate-600">Use the email address from your Never Miss purchase. Only paid customer emails can receive a link.</p>
            <input name="email" type="email" required placeholder="you@yourbusiness.ca" className="mt-6 min-h-12 w-full rounded-xl border border-slate-300 px-4 py-3" />
            <button disabled={busy} className="mt-4 min-h-12 w-full rounded-xl bg-[#071729] px-5 font-semibold text-white disabled:opacity-60">{busy ? "Sending..." : "Send my private link"}</button>
          </form>
        ) : account ? (
          <div className="mt-10 space-y-6">
            <section className="rounded-3xl bg-[#071729] p-7 text-white shadow-xl">
              <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm text-white/60">{account.plan === "never_miss_plus" ? "Never Miss Plus" : "Never Miss"}</p><h2 className="mt-1 text-3xl font-semibold">{account.business_name}</h2></div><span className={`rounded-full px-4 py-2 text-sm font-semibold ${["active", "trialing"].includes(account.status) ? "bg-emerald-300 text-emerald-950" : "bg-amber-200 text-amber-950"}`}>{account.status === "trialing" ? "Free trial active" : account.status}</span></div>
              <p className="mt-6 text-sm text-white/60">Private routing number</p><p className="mt-1 text-2xl font-semibold">{account.assigned_phone || "Not provisioned"}</p>
              {account.trial_ends_at ? <p className="mt-4 rounded-xl bg-white/10 p-3 text-sm text-white/80">Your free trial ends {new Date(account.trial_ends_at).toLocaleDateString()}. Cancel before then to avoid the first monthly charge.</p> : null}
              {account.cancel_at_period_end && account.current_period_ends_at ? <p className="mt-4 rounded-xl bg-amber-100/15 p-3 text-sm text-amber-100">Cancellation is scheduled. Automatic replies remain available until {new Date(account.current_period_ends_at).toLocaleDateString()}.</p> : null}
            </section>
            <section className="rounded-3xl bg-white p-7 shadow-xl">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div><h2 className="text-2xl font-semibold">Service check</h2><p className="mt-2 text-slate-600">A simple view of what Never Miss can see right now.</p></div>
                <span className={`rounded-full px-4 py-2 text-sm font-semibold ${account.recovery_test ? "bg-emerald-100 text-emerald-900" : "bg-amber-100 text-amber-900"}`}>{account.recovery_test ? "Recovery test verified" : account.setup_ready ? "Test required" : "Setup needs attention"}</span>
              </div>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <StatusCard label="Calls detected this month" value={account.calls_this_month} />
                <StatusCard label="Automatic texts sent" value={account.messages_this_month} />
                <StatusCard label="Last call detected" value={account.last_call_at ? new Date(account.last_call_at).toLocaleString() : "No call yet"} />
              </div>
              <div className="mt-5 rounded-2xl bg-slate-50 p-5 text-sm leading-6 text-slate-700">
                <p className="font-semibold text-[#071729]">Finish your connection test</p>
                <ol className="mt-2 space-y-1"><li>1. Call your normal business number from another phone.</li><li>2. Let it ring without answering until the call ends.</li><li>3. Wait for the automatic text, reply to it, then refresh this page.</li></ol>
                <p className="mt-3 text-slate-500">If no call appears here, unanswered-call forwarding is not connected yet.</p>
              </div>
              {account.recovery_test ? <p className="mt-4 rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-900">Verified {new Date(account.recovery_test.verified_at).toLocaleString()}. This records that the forwarding path, recovery text, and callback task were checked together.</p> : account.recent_recovery_tests.length > 0 ? <div className="mt-5 rounded-2xl border border-cyan-200 bg-cyan-50 p-5"><p className="font-semibold">Confirm the completed test</p><p className="mt-1 text-sm text-slate-700">Only confirm after you received the recovery text and saw the callback task.</p>{account.recent_recovery_tests.filter(test => test.callback_task_created).map(test => <button key={test.call_public_uuid} disabled={busy} onClick={() => void confirmRecoveryTest(test.call_public_uuid)} className="mt-3 rounded-xl bg-[#071729] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">Confirm recovery for call detected {new Date(test.detected_at).toLocaleString()}</button>)}</div> : null}
            </section>
            <form onSubmit={save} className="space-y-5 rounded-3xl bg-white p-7 shadow-xl">
              <h2 className="text-2xl font-semibold">Service settings</h2>
              <Field label="Business number customers call" name="existing_business_phone" defaultValue={account.existing_business_phone} />
              <Field label="Mobile number for alerts" name="notification_phone" defaultValue={account.notification_phone} />
              <Field label="Website" name="website_url" type="url" defaultValue={account.website_url} />
              <label className="block"><span className="font-semibold">Automatic reply</span><textarea name="recovery_message" required minLength={20} maxLength={500} defaultValue={account.recovery_message} className="mt-2 min-h-32 w-full rounded-xl border border-slate-300 px-4 py-3" /></label>
              <div className="flex items-start gap-3 rounded-2xl bg-slate-50 p-4"><input id="never-miss-enabled" aria-label="Automatic replies are on" name="enabled" type="checkbox" defaultChecked={account.enabled} className="mt-1" /><div><label htmlFor="never-miss-enabled" className="font-semibold">Automatic replies are on</label><p className="mt-1 text-sm text-slate-600">Turn this off to pause Never Miss without changing your billing.</p></div></div>
              <button disabled={busy} className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#071729] px-5 font-semibold text-white disabled:opacity-60"><Save className="h-5 w-5" />{busy ? "Saving..." : "Save changes"}</button>
            </form>
            <section className="rounded-3xl bg-white p-7 shadow-xl">
              <h2 className="text-2xl font-semibold">Billing and cancellation</h2>
              <p className="mt-2 text-slate-600">Update your card, download invoices, or cancel securely through Stripe.</p>
              {account.billing_portal_available ? <button disabled={busy} onClick={() => void openBillingPortal()} className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border border-slate-300 px-5 font-semibold hover:bg-slate-50 disabled:opacity-60"><CreditCard className="h-5 w-5" />Manage billing with Stripe</button> : <p className="mt-5 rounded-xl bg-amber-50 p-4 text-amber-900">Online billing management is being prepared. Contact hello@pacificnorthsystems.com for immediate help.</p>}
              <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5"><div className="flex gap-2 font-semibold text-amber-950"><PauseCircle className="h-5 w-5" />If you cancel</div><p className="mt-2 text-sm leading-6 text-amber-900">Cancel before the end of the free trial to avoid the first monthly charge. If you cancel a paid subscription, service continues to the end of the current billing period. Remove unanswered call forwarding when service ends so callers return to your normal voicemail.</p></div>
            </section>
            <section className="rounded-3xl border border-cyan-200 bg-cyan-50 p-7">
              <div className="flex gap-3"><Headphones className="mt-1 h-6 w-6 text-[#0b6575]" /><div><h2 className="text-xl font-semibold">Need help?</h2><p className="mt-2 text-slate-700">Send us a message and include your business name. We will help with forwarding, voicemail, testing, or billing.</p><a className="mt-4 inline-flex min-h-12 items-center rounded-xl bg-[#071729] px-5 font-semibold text-white" href={`mailto:${account.support_email}?subject=Never%20Miss%20support%20for%20${encodeURIComponent(account.business_name || "my business")}`}>Email support</a></div></div>
            </section>
          </div>
        ) : null}
      </Container>
    </main>
  );
}

function Field({ label, name, ...props }: { label: string; name: string } & React.ComponentPropsWithoutRef<"input">) {
  return <label className="block"><span className="font-semibold">{label}</span><input name={name} {...props} className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 px-4 py-3" /></label>;
}

function StatusCard({ label, value }: { label: string; value: string | number }) {
  return <div className="rounded-2xl border border-slate-200 p-4"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-[#071729]">{value}</p></div>;
}
