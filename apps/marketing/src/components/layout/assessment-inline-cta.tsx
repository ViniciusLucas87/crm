import { Button } from "@/components/ui/button";

export function AssessmentInlineCTA() {
  return (
    <div className="max-w-[680px] mx-auto text-center px-4">
      <div className="bg-pns-soft-blue/60 rounded-[20px] border border-pns-text-primary/6 p-6 sm:p-8">
        <p className="text-[15px] font-medium text-pns-text-primary">
          Think your business has similar challenges?
        </p>
        <p className="mt-2 text-[14px] text-pns-text-muted">
          Take the free Business Automation Assessment. It takes less than 3 minutes.
        </p>
        <ul className="mt-3 flex flex-wrap justify-center gap-x-5 gap-y-1 text-[13px] text-pns-text-muted">
          <li className="flex items-center gap-1.5">
            <span className="text-pns-text-primary/50 text-[10px]">✓</span>
            Estimated time savings
          </li>
          <li className="flex items-center gap-1.5">
            <span className="text-pns-text-primary/50 text-[10px]">✓</span>
            Automation opportunities
          </li>
          <li className="flex items-center gap-1.5">
            <span className="text-pns-text-primary/50 text-[10px]">✓</span>
            Personalized roadmap
          </li>
        </ul>
        <div className="mt-5">
          <Button variant="primary" size="default" href="/assessment" className="!rounded-xl !font-semibold">
            Start Assessment
          </Button>
        </div>
      </div>
    </div>
  );
}
