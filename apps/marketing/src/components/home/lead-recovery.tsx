import Image from "next/image";
import { Check, PhoneIncoming } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";

const capabilities = [
  "Detects an unanswered business call",
  "Sends a thoughtful text response within moments",
  "Records the caller and interaction in your CRM",
  "Creates a clear callback task for your team",
  "Prevents duplicate messages and keeps an audit trail",
];

export function LeadRecovery() {
  return (
    <Section variant="dark" id="missed-call-lead-recovery">
      <Container>
        <div className="grid items-center gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-sm font-medium text-pns-text-soft-white">
              <PhoneIncoming className="h-4 w-4" aria-hidden="true" />
              Missed Call Lead Recovery
            </div>
            <h2 className="mt-5 text-[clamp(2rem,4vw,3.25rem)] font-bold leading-tight text-pns-text-soft-white">
              Never let a missed call become a missed customer
            </h2>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-pns-text-light">
              When you cannot answer, your business can still respond with care.
              We build a complete recovery system that acknowledges the caller,
              saves the opportunity and reminds your team to call back.
            </p>

            <ul className="mt-7 space-y-3">
              {capabilities.map((capability) => (
                <li key={capability} className="flex items-start gap-3 text-pns-text-light">
                  <span className="mt-0.5 rounded-full bg-cyan-300/15 p-1 text-cyan-200">
                    <Check className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <span>{capability}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button variant="primary" size="default" href="/assessment" className="bg-white !text-pns-text-primary hover:bg-white/90">
                See what your business could recover
              </Button>
              <Button variant="outline" size="default" href="/solutions#missed-call-lead-recovery" className="border-white/30 !text-white hover:bg-white/10">
                Explore the system
              </Button>
            </div>
          </div>

          <figure>
            <div className="overflow-hidden rounded-[22px] border border-white/15 bg-white/5 p-2 shadow-2xl shadow-cyan-950/30">
              <Image
                src="/images/missed-call-lead-recovery.png"
                alt="A real Pacific North Systems missed call followed by an automatic customer care text message"
                width={1536}
                height={1024}
                className="h-auto w-full rounded-[16px]"
                sizes="(max-width: 1024px) 100vw, 55vw"
                priority={false}
              />
            </div>
            <figcaption className="mt-3 text-center text-sm text-pns-text-light/80">
              Real proof from the system we use at Pacific North Systems
            </figcaption>
          </figure>
        </div>
      </Container>
    </Section>
  );
}
