import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/cn";
import type { TestimonialData } from "@/lib/testimonials";

interface TestimonialCardProps {
  testimonial: TestimonialData;
  variant?: "light" | "dark";
}

export function TestimonialCard({
  testimonial,
  variant = "light",
}: TestimonialCardProps) {
  const {
    quote,
    clientName,
    clientRole,
    companyName,
    companyLogo,
    companyLogoAlt,
    projectLabel,
    projectUrl,
  } = testimonial;

  return (
    <blockquote
      className={cn(
        "rounded-[24px] border p-8 lg:p-12",
        variant === "light"
          ? "bg-white border-pns-text-primary/8"
          : "bg-[#071B33] border-white/10 text-white",
      )}
    >
      {/* Logo */}
      <div className="mb-8">
        <div className="relative h-[192px] w-auto max-w-[840px]">
          <Image
            src={companyLogo}
            alt={companyLogoAlt}
            width={840}
            height={192}
            className="h-[192px] w-auto object-contain object-left"
          />
        </div>

        {projectLabel && (
          <p
            className={cn(
              "mt-2 text-xs font-medium uppercase tracking-wide",
              variant === "light" ? "text-pns-text-muted" : "text-pns-text-footer-muted",
            )}
          >
            {projectUrl ? (
              <Link
                href={projectUrl}
                className="hover:underline underline-offset-4"
              >
                {projectLabel}
              </Link>
            ) : (
              projectLabel
            )}
          </p>
        )}
      </div>

      {/* Quote */}
      <div className="space-y-4">
        {quote.split("\n\n").map((paragraph, i) => (
          <p
            key={i}
            className={cn(
              "text-base lg:text-lg leading-relaxed",
              variant === "light" ? "text-pns-text-muted" : "text-pns-text-light",
            )}
          >
            {paragraph}
          </p>
        ))}
      </div>

      {/* Attribution */}
      <footer className="mt-8 pt-6 border-t border-current/10">
        <cite className="not-italic">
          <span
            className={cn(
              "block font-bold",
              variant === "light" ? "text-pns-text-primary" : "text-white",
            )}
          >
            {clientName}
          </span>
          <span
            className={cn(
              "block text-sm mt-0.5",
              variant === "light" ? "text-pns-text-muted" : "text-pns-text-footer-muted",
            )}
          >
            {clientRole}, {companyName}
          </span>
        </cite>
      </footer>
    </blockquote>
  );
}
