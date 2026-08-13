import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";
import { Badge } from "@/components/ui/badge";

const industries = [
  "Construction",
  "Property Management",
  "Restoration",
  "Trades",
  "Logistics",
  "Manufacturing",
  "Engineering",
  "Architecture",
];

export function Industries() {
  return (
    <Section variant="white" id="industries">
      <Container>
        <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary text-center">
          Built for teams with complex operations
        </h2>

        <div className="mt-10 flex flex-wrap justify-center gap-3">
          {industries.map((industry) => (
            <Badge
              key={industry}
              variant="outline"
              className="px-5 py-2.5 text-sm"
            >
              {industry}
            </Badge>
          ))}
        </div>
      </Container>
    </Section>
  );
}
