import Image from "next/image";
import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";
import { Cpu, HardHat, Handshake } from "lucide-react";

const founderCards = [
  {
    icon: Cpu,
    title: "Technical leader",
    description: "Experience building software tools and automation.",
  },
  {
    icon: HardHat,
    title: "Operations aware",
    description: "Practical understanding of field operations.",
  },
  {
    icon: Handshake,
    title: "Hands-on partner",
    description: "Direct access, clear communication, and fast iteration.",
  },
];

export function Founder() {
  return (
    <Section variant="white" id="about">
      <Container>
        <div className="flex flex-col lg:flex-row gap-12 lg:gap-20 items-center">
          {/* Text side */}
          <div className="flex-1">
            <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary">
              Founder led delivery
            </h2>
            <p className="mt-4 text-pns-text-muted leading-relaxed max-w-xl">
              Pacific North Systems is led by Vini Dias, a former Electronic
              Arts Tech Lead with experience building internal tools, automation
              systems, production pipelines, and developer productivity
              software. This technical foundation is combined with practical,
              hands-on experience in field operations.
            </p>

            <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-6">
              {founderCards.map((card) => (
                <div key={card.title}>
                  <card.icon
                    className="w-8 h-8 text-pns-text-muted mb-3"
                    aria-hidden="true"
                  />
                  <h3 className="font-bold text-pns-text-primary">
                    {card.title}
                  </h3>
                  <p className="mt-1 text-sm text-pns-text-muted">
                    {card.description}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-8 pt-6 border-t border-pns-text-primary/10">
              <p className="font-bold text-pns-text-primary">Vini Dias</p>
              <p className="text-sm text-pns-text-muted">
                Pacific North Systems
              </p>
              <p className="text-sm text-pns-text-muted">
                Former Electronic Arts Tech Lead
              </p>
            </div>
          </div>

          {/* Image side */}
          <div className="lg:w-[400px] shrink-0">
            <div className="aspect-[3/4] rounded-[24px] overflow-hidden bg-pns-soft-blue">
              <Image
                src="/images/founder.jpg"
                alt="Vini Dias , Founder & Technical Lead, Pacific North Systems"
                width={400}
                height={533}
                className="w-full h-full object-cover"
                priority
              />
            </div>
          </div>
        </div>
      </Container>
    </Section>
  );
}
