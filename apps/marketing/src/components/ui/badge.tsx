import { cn } from "@/lib/cn";
import type { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline";
}

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        variant === "default" && "bg-pns-accent-light text-pns-text-primary",
        variant === "outline" &&
          "border border-pns-text-primary/15 text-pns-text-muted",
        className,
      )}
      {...props}
    />
  );
}
