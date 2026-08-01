import { cn } from "@/lib/cn";
import type { HTMLAttributes } from "react";

interface SectionProps extends HTMLAttributes<HTMLElement> {
  variant?: "default" | "dark" | "soft" | "white";
  as?: "section" | "div";
}

export function Section({
  className,
  variant = "default",
  as: Component = "section",
  ...props
}: SectionProps) {
  return (
    <Component
      className={cn(
        "py-20 lg:py-24",
        variant === "default" && "bg-pns-bg",
        variant === "dark" && "bg-pns-dark-hero text-pns-text-light",
        variant === "soft" && "bg-pns-soft-blue",
        variant === "white" && "bg-pns-white",
        className,
      )}
      {...props}
    />
  );
}
