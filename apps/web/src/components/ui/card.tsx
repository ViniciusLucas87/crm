"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/cn";

type CardProps = {
  className?: string;
  children: ReactNode;
};

export function Card({ className, children }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur",
        className
      )}
    >
      {children}
    </div>
  );
}
