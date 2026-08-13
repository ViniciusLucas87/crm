"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/cn";
import { siteConfig } from "@/lib/site-config";
import { Button } from "@/components/ui/button";

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <header
      className="sticky top-0 z-50 border-b border-black/8 bg-white/95 backdrop-blur-[12px]"
      role="banner"
    >
      <div className="w-full max-w-[1440px] pl-6 sm:pl-8 lg:pl-16 xl:pl-20 pr-6 sm:pr-8 lg:pr-12 xl:pr-16">
        <nav
          className="flex items-center justify-between h-[72px] lg:h-[80px]"
          aria-label="Main navigation"
        >
          {/* Logo */}
          <Link
            href="/"
            className="shrink-0"
            aria-label="Pacific North Systems home"
          >
            <Image
              src="/images/logo.png"
              alt="Pacific North Systems"
              width={220}
              height={48}
              className="h-[76px] lg:h-[82px] w-auto"
              style={{ width: "auto" }}
              priority
            />
          </Link>

          {/* Desktop nav */}
          <div className="hidden lg:flex items-center gap-10">
            {siteConfig.nav.primary.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-[16px] font-bold transition-colors",
                  "text-pns-text-muted hover:text-pns-text-primary",
                )}
              >
                {item.label}
              </Link>
            ))}
            <Button
              variant="primary"
              size="sm"
              href={siteConfig.nav.cta.href}
              className="!text-[14px] !rounded-lg !font-bold"
            >
              {siteConfig.nav.cta.label}
            </Button>
          </div>

          {/* Mobile hamburger */}
          <button
            className="lg:hidden p-2 -mr-2 text-pns-text-primary transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-expanded={mobileOpen}
            aria-controls="mobile-menu"
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
          >
            {mobileOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </nav>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          id="mobile-menu"
          className="fixed inset-x-0 top-[72px] h-[calc(100dvh-72px)] overflow-y-auto overscroll-contain bg-white lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation"
        >
          <div className="flex flex-col gap-1 p-6">
            {siteConfig.nav.primary.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="py-4 text-lg font-medium text-pns-text-primary hover:text-pns-text-muted transition-colors"
                onClick={() => setMobileOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <div className="mt-6 pt-6 border-t border-black/10">
              <Button
                variant="primary"
                size="default"
                href={siteConfig.nav.cta.href}
                className="w-full !rounded-lg"
                onClick={() => setMobileOpen(false)}
              >
                {siteConfig.nav.cta.label}
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
