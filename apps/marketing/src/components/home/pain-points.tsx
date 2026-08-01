import { Section } from "@/components/ui/section";
import { Container } from "@/components/ui/container";
import {
  Copy,
  FileText,
  GitBranch,
  ImageIcon,
  Clock,
  Search,
} from "lucide-react";

const painPoints = [
  {
    icon: Copy,
    title: "Repetitive data entry",
    description: "Replace duplicate typing across tools.",
  },
  {
    icon: FileText,
    title: "Paper inspections and manual reports",
    description: "Turn field notes into structured digital reports.",
  },
  {
    icon: GitBranch,
    title: "Duplicate work between systems",
    description: "Connect your tools so your team enters information once.",
  },
  {
    icon: ImageIcon,
    title: "Lost photos and documents",
    description: "Keep job evidence organized by project.",
  },
  {
    icon: Clock,
    title: "Slow approvals and status updates",
    description: "Move requests, reviews, and decisions faster.",
  },
  {
    icon: Search,
    title: "Searching through files, PDFs, and emails",
    description: "Find the right information without digging.",
  },
];

export function PainPoints() {
  return (
    <Section variant="white" id="pain-points">
      <Container>
        {/* Heading , left-aligned, editorial style matching hero */}
        <div>
          <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary leading-[1.15] tracking-[-0.01em]">
            Your team should not be running operations from spreadsheets, PDFs,
            and email chains.
          </h2>
          <p className="mt-4 text-[1.0625rem] text-pns-text-muted max-w-2xl leading-relaxed">
            Repetitive manual work costs more than time , it costs accuracy,
            consistency, and the attention your team should be spending on the
            work that matters.
          </p>
        </div>

        {/* Grid , 3 columns, generous spacing */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {painPoints.map((point) => (
            <div
              key={point.title}
              className="group flex gap-5 p-7 rounded-[20px] border border-pns-text-primary/6 bg-white transition-all duration-300 hover:shadow-lg hover:shadow-black/[0.04] hover:border-pns-text-primary/12 hover:-translate-y-0.5"
            >
              <div className="shrink-0 w-10 h-10 rounded-xl bg-pns-soft-blue flex items-center justify-center transition-colors duration-300 group-hover:bg-pns-accent-light">
                <point.icon
                  className="w-5 h-5 text-pns-text-muted transition-colors duration-300 group-hover:text-pns-text-primary"
                  aria-hidden="true"
                />
              </div>
              <div>
                <h3 className="font-semibold text-pns-text-primary text-[15px] leading-snug">
                  {point.title}
                </h3>
                <p className="mt-1.5 text-sm text-pns-text-muted leading-relaxed">
                  {point.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
