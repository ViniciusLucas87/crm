import type { Metadata } from "next";
import { AssessmentFlow } from "@/components/assessment";

export const metadata: Metadata = {
  title: "Operations Assessment | Pacific North Systems",
  description:
    "A fast, 2-minute business diagnostic. Identify your biggest operational time drains and estimate potential savings.",
  alternates: { canonical: "/assessment" },
};

export default function AssessmentPage() {
  return (
    <main className="pt-24 pb-16 min-h-screen bg-pns-bg">
      <div className="text-center mb-8 px-4">
        <h1 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary">
          Operations Assessment
        </h1>
        <p className="mt-3 text-pns-text-muted max-w-xl mx-auto">
          A quick diagnostic that identifies where automation could save your team the most time. Takes about 2 minutes.
        </p>
      </div>
      <AssessmentFlow />
    </main>
  );
}

