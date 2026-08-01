"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

export function FloatingCTA() {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  if (dismissed) return null;

  return (
    <div
      className={`fixed bottom-6 right-6 z-40 transition-all duration-500 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
    >
      <div className="flex items-center gap-3 bg-white rounded-[16px] shadow-lg border border-pns-text-primary/10 px-5 py-3.5">
        <Button
          variant="primary"
          size="sm"
          href="/assessment"
          className="!text-[14px] !rounded-xl !font-semibold"
        >
          Find Your Biggest Time Drain
        </Button>
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss"
          className="shrink-0 w-6 h-6 rounded-full bg-pns-text-primary/5 flex items-center justify-center hover:bg-pns-text-primary/10 transition-colors"
        >
          <X className="w-3.5 h-3.5 text-pns-text-muted" />
        </button>
      </div>
    </div>
  );
}
