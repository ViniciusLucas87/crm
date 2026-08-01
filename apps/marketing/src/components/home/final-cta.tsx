import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site-config";

export function FinalCTA() {
  return (
    <Section variant="dark" id="contact">
      <Container>
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-soft-white">
            Let&apos;s identify the process wasting the most time inside your
            business.
          </h2>
          <p className="mt-4 text-pns-text-light leading-relaxed">
            Book an in-person audit or a call, and we&apos;ll review your
            operations together to identify where to start.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              variant="primary"
              size="lg"
              href={siteConfig.contact.calendlyAudit}
              external
              className="bg-white !text-pns-text-primary hover:bg-white/90"
            >
              Book a 30-minute Operations Audit
            </Button>
            <a
              href={`mailto:${siteConfig.contact.email}`}
              className="text-pns-text-light hover:text-pns-text-soft-white underline underline-offset-4 transition-colors"
            >
              {siteConfig.contact.email}
            </a>
          </div>
        </div>
      </Container>
    </Section>
  );
}
