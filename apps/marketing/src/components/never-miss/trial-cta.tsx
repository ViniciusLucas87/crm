"use client";

import { useEffect } from "react";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { Button } from "@/components/ui/button";

type PlanKey = "never-miss" | "never-miss-plus";

type Gtag = (command: "event", eventName: string, parameters?: Record<string, unknown>) => void;

declare global {
  interface Window {
    gtag?: Gtag;
  }
}

function track(eventName: string, plan: PlanKey, value: number) {
  window.gtag?.("event", eventName, {
    currency: "CAD",
    value,
    items: [{ item_id: plan, item_name: plan === "never-miss-plus" ? "Never Miss Plus" : "Never Miss", price: value, quantity: 1 }],
  });
}

export function TrialCta({
  plan = "never-miss",
  available,
  label,
  className,
}: {
  plan?: PlanKey;
  available: boolean;
  label: string;
  className?: string;
}) {
  const price = plan === "never-miss-plus" ? 89 : 39;
  const href = available ? `/never-miss/checkout?plan=${plan}` : "/contact";

  return (
    <Button
      href={href}
      size="lg"
      className={className}
      onClick={() => track(available ? "select_never_miss_plan" : "request_never_miss_setup", plan, price)}
    >
      {label} <ArrowRight className="h-4 w-4" />
    </Button>
  );
}

export function CheckoutButton({ checkoutUrl, plan }: { checkoutUrl: string; plan: PlanKey }) {
  const price = plan === "never-miss-plus" ? 89 : 39;
  const conversionLabel = process.env.NEXT_PUBLIC_GOOGLE_ADS_TRIAL_CHECKOUT_LABEL?.trim();
  const googleAdsId = process.env.NEXT_PUBLIC_GOOGLE_ADS_ID?.trim();

  function recordCheckoutStart() {
    track("begin_checkout", plan, price);
    if (googleAdsId && conversionLabel) {
      window.gtag?.("event", "conversion", {
        send_to: `${googleAdsId}/${conversionLabel}`,
        value: price,
        currency: "CAD",
      });
    }
  }

  return (
    <a
      href={checkoutUrl}
      rel="noreferrer"
      onClick={recordCheckoutStart}
      className="flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#071729] px-6 py-3 text-center text-base font-semibold text-white transition hover:bg-[#0b6575]"
    >
      <LockKeyhole className="h-5 w-5" /> Start secure free test
    </a>
  );
}

export function ActivationMeasurement({ checkoutSessionId }: { checkoutSessionId: string | null }) {
  const conversionLabel = process.env.NEXT_PUBLIC_GOOGLE_ADS_TRIAL_ACTIVATION_LABEL?.trim();
  const googleAdsId = process.env.NEXT_PUBLIC_GOOGLE_ADS_ID?.trim();

  useEffect(() => {
    if (!checkoutSessionId) return;
    const storageKey = `never-miss-activation:${checkoutSessionId}`;
    if (window.sessionStorage.getItem(storageKey)) return;
    window.sessionStorage.setItem(storageKey, "recorded");

    window.gtag?.("event", "trial_activation_completed", { currency: "CAD" });
    if (googleAdsId && conversionLabel) {
      window.gtag?.("event", "conversion", { send_to: `${googleAdsId}/${conversionLabel}` });
    }
  }, [checkoutSessionId, conversionLabel, googleAdsId]);

  return null;
}
