"use client";

import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "rounded-xl bg-cyan-400/15 px-4 py-2.5 text-sm font-medium text-cyan-200 transition hover:bg-cyan-400/25 focus-visible:ring-2 focus-visible:ring-cyan-400/50 disabled:opacity-40",
  secondary:
    "rounded-xl border border-white/10 px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:border-white/20 hover:text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50 disabled:opacity-30",
  ghost:
    "rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-300 transition hover:border-white/20 hover:bg-white/5 hover:text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50 disabled:opacity-40",
  danger:
    "rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-300 transition hover:border-amber-400/30 hover:bg-amber-950/20 hover:text-amber-300 focus-visible:ring-2 focus-visible:ring-amber-400/50 disabled:opacity-40",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "secondary", className, children, ...props }, ref) => {
    return (
      <button ref={ref} className={cn(variantStyles[variant], className)} {...props}>
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
