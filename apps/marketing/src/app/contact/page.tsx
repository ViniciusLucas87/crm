import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site-config";
import { Mail, Phone, MapPin, Calendar } from "lucide-react";

export const metadata: Metadata = {
  title: "Contact",
  description:
    "Get in touch with Pacific North Systems. Book an Operations Audit, email us, or call to discuss custom software and automation for your Vancouver or Victoria business.",
  openGraph: {
    title: "Contact Pacific North Systems",
    description:
      "Book an Operations Audit or reach out to discuss custom software, workflow automation, and AI-powered systems for your business.",
  },
};

const contactItems = [
  {
    icon: Calendar,
    label: "Book an Operations Audit",
    description: "Schedule a 30-minute call or in-person visit to review your workflows.",
    action: {
      label: "Book a 30-minute Operations Audit",
      href: siteConfig.contact.calendlyAudit,
      external: true,
    },
  },
  {
    icon: Mail,
    label: "Email",
    description: "Reach us directly for questions about our services or to start a conversation.",
    action: {
      label: siteConfig.contact.email,
      href: `mailto:${siteConfig.contact.email}`,
    },
  },
  {
    icon: Phone,
    label: "Phone",
    description: "Prefer to talk? Call us during business hours, Pacific Time.",
    action: {
      label: siteConfig.contact.phone,
      href: `tel:${siteConfig.contact.phone.replace(/[^+\d]/g, "")}`,
    },
  },
  {
    icon: MapPin,
    label: "Location",
    description: "Based in Kitsilano, serving Metro Vancouver, Victoria, and across British Columbia.",
  },
];

export default function ContactPage() {
  return (
    <main className="pt-28 pb-16 lg:pt-32 lg:pb-20">
      <Container size="narrow">
        <div className="max-w-[720px] mx-auto">
          <h1 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary">
            Let&apos;s talk about your operations.
          </h1>
          <p className="mt-4 text-pns-text-muted leading-relaxed">
            Every operations-heavy business has processes that could run more
            smoothly. Tell us what&apos;s slowing your team down, and
            we&apos;ll figure out where to start.
          </p>

          <div className="mt-12 grid gap-6">
            {contactItems.map((item) => (
              <div
                key={item.label}
                className="flex items-start gap-4 p-6 rounded-[16px] bg-white border border-pns-text-primary/8"
              >
                <div className="w-10 h-10 rounded-[10px] bg-pns-soft-blue flex items-center justify-center shrink-0">
                  <item.icon className="w-5 h-5 text-pns-text-primary" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-base font-semibold text-pns-text-primary">
                    {item.label}
                  </h2>
                  <p className="mt-1 text-sm text-pns-text-muted leading-relaxed">
                    {item.description}
                  </p>
                  {"action" in item && item.action && (
                    <div className="mt-3">
                      {item.action.external ? (
                        <Button
                          variant="primary"
                          href={item.action.href}
                          external
                        >
                          {item.action.label}
                        </Button>
                      ) : (
                        <a
                          href={item.action.href}
                          className="text-sm font-medium text-pns-text-primary underline underline-offset-4 hover:text-pns-text-primary/80 transition-colors"
                        >
                          {item.action.label}
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 p-8 rounded-[16px] bg-pns-soft-blue text-center">
            <h2 className="text-xl font-bold text-pns-text-primary">
              Want us to come to you?
            </h2>
            <p className="mt-2 text-pns-text-muted max-w-md mx-auto">
              We offer in-person Operations Audits for businesses in Metro
              Vancouver and Greater Victoria. We&apos;ll visit your office, walk
              your workflows, and identify practical improvements you can act on.
            </p>
            <div className="mt-6">
              <Button
                variant="primary"
                href={siteConfig.contact.calendlyAudit}
                external
              >
                Schedule an In-Person Audit
              </Button>
            </div>
          </div>
        </div>
      </Container>
    </main>
  );
}
