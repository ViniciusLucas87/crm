import Image from "next/image";
import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";

const demos = [
  {
    image: "/images/demo-inspection.png",
    title: "Inspection & Reporting System",
    description:
      "Mobile inspections, photos, notes, signatures, and automated PDF reports.",
    link: "/solutions#inspection-software",
  },
  {
    image: "/images/demo-property.png",
    title: "Property Move-in / Move-out System",
    description:
      "Digital checklists, signatures, photos, and maintenance tracking in one place.",
    link: "/solutions#custom-business-software",
  },
  {
    image: "/images/demo-ai-docs.png",
    title: "AI Document Assistant",
    description:
      "Search documents, extract information, and generate reports in seconds.",
    link: "/solutions#ai-document-processing",
  },
  {
    image: "/images/demo-dashboard.png",
    title: "Smart Business Software",
    description:
      "Systems that help you make better decisions and build measurable operational capacity.",
    link: "/solutions#business-dashboards",
  },
  {
    image: "/images/demo-crm.png",
    title: "Custom CRM",
    description:
      "Manage clients, budgets, sales, and leads in a company-owned CRM built around the information your team actually needs.",
    link: "/solutions#crm-development",
  },
];

export function DemoSystems() {
  return (
    <Section variant="soft" id="demo-systems">
      <Container>
        <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary">
          Demo Systems
        </h2>
        <p className="mt-4 text-pns-text-muted max-w-2xl">
          Examples of practical systems we can build and customize for your
          operation.
        </p>

        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {demos.map((demo) => (
            <div
              key={demo.title}
              className="flex flex-col rounded-[16px] bg-white border border-pns-text-primary/8 overflow-hidden group hover:shadow-md transition-shadow"
            >
              <div className="aspect-[16/10] bg-pns-soft-blue relative overflow-hidden">
                <Image
                  src={demo.image}
                  alt={demo.title}
                  fill
                  className="object-cover group-hover:scale-[1.03] transition-transform duration-500"
                  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                />
              </div>
              <div className="flex flex-col p-5 flex-1">
                <h3 className="font-bold text-pns-text-primary text-lg">
                  {demo.title}
                </h3>
                <p className="mt-1.5 text-sm text-pns-text-muted leading-relaxed flex-1">
                  {demo.description}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  href={demo.link}
                  className="mt-4 self-start"
                >
                  Explore {demo.title.split(" ")[0].toLowerCase()} software
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Button variant="secondary" size="default" href="/solutions">
            View All Solutions
          </Button>
        </div>
      </Container>
    </Section>
  );
}
