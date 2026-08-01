import { cn } from "@/lib/cn";
import type { ButtonHTMLAttributes, AnchorHTMLAttributes } from "react";
import Link from "next/link";

type ButtonBaseProps = {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "default" | "lg" | "sm";
};

type ButtonAsButton = ButtonBaseProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    href?: never;
  };

type ButtonAsLink = ButtonBaseProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    external?: boolean;
  };

type ButtonProps = ButtonAsButton | ButtonAsLink;

export function Button({
  variant = "primary",
  size = "default",
  className,
  ...props
}: ButtonProps) {
  const baseStyles = cn(
    "inline-flex items-center justify-center gap-2 rounded-lg font-bold transition-all duration-200 focus-visible:outline-2 focus-visible:outline-offset-2",
    "min-h-[44px]", // touch target
    variant === "primary" &&
      "bg-pns-text-primary text-white hover:bg-pns-text-primary-alt",
    variant === "secondary" &&
      "bg-pns-accent-light text-pns-text-primary hover:bg-pns-accent-light/70",
    variant === "outline" &&
      "border border-pns-text-primary/20 text-pns-text-primary hover:bg-pns-text-primary/5",
    variant === "ghost" && "text-pns-text-primary hover:bg-pns-text-primary/5",
    size === "default" && "px-6 py-3 text-sm",
    size === "lg" && "px-8 py-4 text-base",
    size === "sm" && "px-4 py-2 text-xs",
    className,
  );

  if ("href" in props && props.href) {
    const { href, external, ...anchorProps } = props as ButtonAsLink;
    const isExternal =
      external ?? (href.startsWith("http") || href.startsWith("mailto"));

    if (isExternal) {
      return (
        <a
          href={href}
          className={baseStyles}
          target="_blank"
          rel="noopener noreferrer"
          {...anchorProps}
        >
          {anchorProps.children}
        </a>
      );
    }

    return (
      <Link href={href} className={baseStyles} {...anchorProps}>
        {anchorProps.children}
      </Link>
    );
  }

  return (
    <button
      className={baseStyles}
      {...(props as ButtonAsButton)}
    />
  );
}
