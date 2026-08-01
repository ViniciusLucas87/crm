import type { FAQItem } from "@/lib/blog-types";

interface FAQProps {
  items: FAQItem[];
}

export function BlogFAQ({ items }: FAQProps) {
  if (!items || items.length === 0) return null;

  return (
    <section className="mt-12 pt-8 border-t border-pns-text-primary/10">
      <h2 className="text-xl font-bold text-pns-text-primary mb-6">
        Frequently asked questions
      </h2>
      <div className="space-y-4">
        {items.map((item, i) => (
          <details
            key={i}
            className="group rounded-[16px] border border-pns-text-primary/10 bg-white"
          >
            <summary className="cursor-pointer p-5 font-medium text-pns-text-primary list-none flex items-center justify-between">
              {item.question}
              <span className="text-pns-text-muted group-open:rotate-180 transition-transform ml-2 shrink-0">
                ▼
              </span>
            </summary>
            <div className="px-5 pb-5 text-sm text-pns-text-muted leading-relaxed">
              {item.answer}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
