import {
  Hero,
  PainPoints,
  WhatWeBuild,
  Industries,
  DemoSystems,
  LeadRecovery,
  Founder,
  Process,
  FinalCTA,
} from "@/components/home";
import { CustomerShowcase } from "@/components/customer-showcase";
import { AssessmentInlineCTA } from "@/components/layout/assessment-inline-cta";

export default function HomePage() {
  return (
    <>
      <Hero />
      <PainPoints />
      <AssessmentInlineCTA />
      <WhatWeBuild />
      <Industries />
      <DemoSystems />
      <LeadRecovery />
      <AssessmentInlineCTA />
      <Founder />
      <Process />
      <CustomerShowcase />
      <FinalCTA />
    </>
  );
}
