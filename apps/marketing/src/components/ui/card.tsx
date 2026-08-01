import { cn } from "@/lib/cn";
import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "outlined" | "elevated";
}

export function Card({
  className,
  variant = "default",
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-[16px] bg-white p-5",
        variant === "outlined" && "border border-pns-text-primary/10",
        variant === "elevated" && "shadow-sm",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeading({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-lg font-bold text-pns-text-primary", className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardBody({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-pns-text-muted leading-relaxed", className)}
      {...props}
    />
  );
}
