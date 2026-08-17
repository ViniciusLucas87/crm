import type { Metadata } from "next";
import Link from "next/link";
import { Check, LockKeyhole } from "lucide-react";
import { Container } from "@/components/ui/container";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Start Never Miss | Secure Checkout",
  description: "Choose your Never Miss package and complete secure payment.",
  robots: { index: false, follow: false },
};

function trustedStripePaymentLink(value: string | undefined): string | undefined {
  if (!value) return undefined;

  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.hostname !== "buy.stripe.com") return undefined;
    return url.toString();
  } catch {
    return undefined;
  }
}

const plans = {
  "never-miss": {
    name: "Never Miss",
    price: "$39",
    checkoutUrl: trustedStripePaymentLink(process.env.NEVER_MISS_CHECKOUT_URL),
    features: ["Automatic missed call text", "Custom reply message", "Callback reminders", "Missed call history"],
  },
  "never-miss-plus": {
    name: "Never Miss Plus",
    price: "$89",
    checkoutUrl: trustedStripePaymentLink(process.env.NEVER_MISS_PLUS_CHECKOUT_URL),
    features: ["Everything in Never Miss", "One inbox for customer replies", "Website and form inquiries", "Simple follow up tracking"],
  },
} as const;

type PlanKey = keyof typeof plans;

export default async function NeverMissCheckoutPage({
  searchParams,
}: {
  searchParams: Promise<{ plan?: string }>;
}) {
  const requestedPlan = (await searchParams).plan;
  const planKey: PlanKey = requestedPlan === "never-miss-plus" ? "never-miss-plus" : "never-miss";
  const plan = plans[planKey];

  return (
    <main className="bg-[#f4f7f7] py-16 lg:py-24">
      <Container size="narrow">
        <div className="mb-8 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0b6575]">Secure checkout</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">Start {plan.name}</h1>
          <p className="mt-4 text-lg text-pns-text-muted">Cancel anytime. We help connect and test your service after payment.</p>
        </div>

        <div className="overflow-hidden rounded-3xl border border-black/10 bg-white shadow-xl">
          <div className="border-b border-black/10 p-7 sm:p-9">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div><h2 className="text-3xl font-semibold text-pns-text-primary">{plan.name}</h2><p className="mt-2 text-pns-text-muted">Monthly service</p></div>
              <div><span className="text-5xl font-semibold tracking-tight text-pns-text-primary">{plan.price}</span><span className="ml-2 text-pns-text-muted">CAD/month</span></div>
            </div>
            <ul className="mt-7 grid gap-3 sm:grid-cols-2">
              {plan.features.map((feature) => <li key={feature} className="flex gap-3 text-pns-text-primary"><Check className="mt-0.5 h-5 w-5 shrink-0 text-[#0b6575]" />{feature}</li>)}
            </ul>
          </div>

          <div className="p-7 sm:p-9">
            {plan.checkoutUrl ? (
              <a href={plan.checkoutUrl} rel="noreferrer" className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#071729] px-6 py-3 text-center text-base font-semibold text-white transition hover:bg-[#0b6575]">
                <LockKeyhole className="h-5 w-5" /> Continue to secure payment
              </a>
            ) : (
              <div className="rounded-2xl bg-[#edf5f5] p-5 text-center">
                <p className="font-semibold text-pns-text-primary">Online payment is being connected.</p>
                <p className="mt-2 text-pns-text-muted">You can start today by calling {siteConfig.contact.phone} or emailing {siteConfig.contact.email}.</p>
              </div>
            )}
            <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm">
              <Link href={`/never-miss/checkout?plan=${planKey === "never-miss" ? "never-miss-plus" : "never-miss"}`} className="font-semibold text-[#0b6575] hover:underline">Compare the other package</Link>
              <Link href="/never-miss" className="text-pns-text-muted hover:underline">Back to Never Miss</Link>
            </div>
          </div>
        </div>
      </Container>
    </main>
  );
}
