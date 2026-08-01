"use client";

import { type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  /** When true, pads left for a search icon */
  hasLeftIcon?: boolean;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, hasLeftIcon, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 hover:border-white/20 focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/30",
          hasLeftIcon && "pl-9",
          className,
        )}
        {...props}
      />
    );
  },
);

Input.displayName = "Input";
