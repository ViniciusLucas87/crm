"use client";

import { useEffect } from "react";

declare global {
  interface Window {
    dataLayer?: unknown[];
    pnsAnalyticsQueue?: Array<{ event: string; payload: Record<string, unknown> }>;
  }
}

type GoogleTag = (command: string, event: string | Date, params?: Record<string, unknown>) => void;

function googleWindow() {
  return window as Window & { gtag?: GoogleTag };
}

function reportLinkClick(event: MouseEvent) {
  const element = event.target instanceof Element ? event.target.closest("a") : null;
  if (!element) return;

  const href = element.getAttribute("href") || "";
  const eventName = href.startsWith("tel:")
    ? "phone_click"
    : href.startsWith("mailto:")
      ? "email_click"
      : href.includes("calendly.com")
        ? "consultation_booking_click"
        : null;

  if (eventName) googleWindow().gtag?.("event", eventName, { link_url: href });
}

export function GoogleAnalytics() {
  useEffect(() => {
    let disposed = false;
    let clickListenerAttached = false;

    void fetch("/api/analytics-config", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) return null;
        return (await response.json()) as { measurementId?: string };
      })
      .then((config) => {
        if (disposed || !config?.measurementId) return;

        const bootstrapScript = document.createElement("script");
        bootstrapScript.text =
          "window.dataLayer = window.dataLayer || []; window.gtag = function(){window.dataLayer.push(arguments);};";
        document.head.appendChild(bootstrapScript);

        const gaWindow = googleWindow();
        gaWindow.gtag?.("js", new Date());
        gaWindow.gtag?.("config", config.measurementId);

        for (const queued of gaWindow.pnsAnalyticsQueue || []) {
          gaWindow.gtag?.("event", queued.event, queued.payload);
        }
        gaWindow.pnsAnalyticsQueue = [];

        const script = document.createElement("script");
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(config.measurementId)}`;
        document.head.appendChild(script);
        document.addEventListener("click", reportLinkClick);
        clickListenerAttached = true;
      })
      .catch(() => {
        // Analytics must never interfere with the website.
      });

    return () => {
      disposed = true;
      if (clickListenerAttached) document.removeEventListener("click", reportLinkClick);
    };
  }, []);

  return null;
}
