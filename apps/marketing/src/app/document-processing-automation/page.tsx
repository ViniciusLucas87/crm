import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  FileCheck2,
  FileSearch,
  ScanText,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Document Processing Automation in Vancouver",
  description:
    "Automate invoice, form, PDF, and business document processing with reliable extraction, review, and system integration for Vancouver businesses.",
  alternates: { canonical: "/document-processing-automation" },
  openGraph: {
    title: "Document Processing Automation in Vancouver",
    description:
      "Turn recurring invoices, forms, PDFs, and records into structured, reviewable business data.",
    url: "/document-processing-automation",
  },
};

const documentTypes = [
  "Invoices and purchase orders",
  "Applications and intake forms",
  "Inspection reports and field records",
  "Contracts and service documents",
  "Receipts, statements, and supporting files",
  "Recurring PDFs, scans, and email attachments",
];

const steps = [
  {
    icon: FileSearch,
    title: "Capture",
    copy: "Collect documents from the inbox, upload form, shared folder, or the business system your team already uses.",
  },
  {
    icon: ScanText,
    title: "Extract",
    copy: "Read the fields that matter, validate the format, and flag low-confidence or incomplete information for review.",
  },
  {
    icon: FileCheck2,
    title: "Review",
    copy: "Give a person a clear approval step for exceptions, sensitive records, and decisions that require judgement.",
  },
  {
    icon: Workflow,
    title: "Route",
    copy: "Send approved information into accounting, CRM, reporting, or another operational workflow without duplicate entry.",
  },
];

const faqs = [
  {
    question: "What is document processing automation?",
    answer:
      "Document processing automation captures information from documents such as invoices, forms, PDFs, and scans, turns it into structured data, and routes it through a defined business workflow.",
  },
  {
    question: "Can it work with scanned PDFs and different document layouts?",
    answer:
      "Often, yes. The right approach depends on scan quality, layout variation, handwriting, and the fields you need. We test representative documents before recommending an implementation.",
  },
  {
    question: "Does automation remove human review?",
    answer:
      "Not by default. We design review steps around confidence, risk, and business rules so people remain responsible for exceptions and important decisions.",
  },
  {
    question: "Can the results connect to our existing software?",
    answer:
      "Yes, when the destination provides a practical integration path. Processed data can be prepared for accounting, CRM, reporting, document management, or custom operational systems.",
  },
  {
    question: "How do we start?",
    answer:
      "Start with one recurring document type, a defined set of fields, and a measurable manual bottleneck. That creates a focused first version that can be tested against real work.",
  },
];

export default function DocumentProcessingAutomationPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Service",
        "@id": `${siteConfig.url}/document-processing-automation#service`,
        name: "Document Processing Automation",
        serviceType: "Document processing automation",
        provider: { "@id": `${siteConfig.url}/#organization` },
        areaServed: [
          { "@type": "City", name: "Vancouver" },
          { "@type": "Country", name: "Canada" },
        ],
        url: `${siteConfig.url}/document-processing-automation`,
        description:
          "Automation for extracting, reviewing, and routing information from invoices, forms, PDFs, scans, and recurring business documents.",
      },
      {
        "@type": "FAQPage",
        mainEntity: faqs.map((faq) => ({
          "@type": "Question",
          name: faq.question,
          acceptedAnswer: { "@type": "Answer", text: faq.answer },
        })),
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <section className="bg-[#051226] py-20 text-white lg:py-28">
        <Container>
          <div className="max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-300">
              Vancouver document automation services
            </p>
            <h1 className="mt-5 text-[clamp(2.7rem,6vw,5.25rem)] font-semibold leading-[0.98] tracking-[-0.04em]">
              Document processing automation that keeps people in control.
            </h1>
            <p className="mt-7 max-w-3xl text-lg leading-8 text-white/78 sm:text-xl">
              Turn recurring invoices, forms, PDFs, scans, and email attachments into structured,
              reviewable data—then move that information into the systems your team already uses.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button href="/assessment" size="lg" className="bg-white !text-[#051226] hover:bg-white/90">
                Assess your workflow <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                href="/contact?service=document-processing-automation"
                variant="outline"
                size="lg"
                className="border-white/40 !text-white hover:bg-white/10"
              >
                Discuss your documents
              </Button>
            </div>
          </div>
        </Container>
      </section>

      <section className="border-b border-black/8 bg-[#f3f6f7] py-16 lg:py-20">
        <Container>
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.15em] text-[#0b6575]">
                Where it helps
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
                Less retyping. Faster review. Better records.
              </h2>
              <p className="mt-5 text-lg leading-8 text-pns-text-muted">
                The best starting point is a document your team handles repeatedly and a clear
                destination for the information inside it. We map that workflow before choosing
                extraction or AI tools.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {documentTypes.map((type) => (
                <div key={type} className="flex gap-3 rounded-2xl border border-black/8 bg-white p-5 text-pns-text-primary shadow-sm">
                  <Check className="mt-0.5 h-5 w-5 shrink-0 text-[#0b6575]" />
                  <span className="font-medium">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-24">
        <Container>
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-[#0b6575]">A practical workflow</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
              From incoming document to usable business data.
            </h2>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, index) => (
              <article key={step.title} className="rounded-3xl border border-black/10 bg-[#f8fafb] p-6">
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#051226] text-cyan-300">
                    <step.icon className="h-6 w-6" aria-hidden="true" />
                  </span>
                  <span className="text-sm font-semibold text-[#0b6575]">0{index + 1}</span>
                </div>
                <h3 className="mt-6 text-xl font-semibold text-pns-text-primary">{step.title}</h3>
                <p className="mt-3 leading-7 text-pns-text-muted">{step.copy}</p>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="bg-[#eaf4f4] py-20 lg:py-24">
        <Container>
          <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.15em] text-[#0b6575]">Start with one document type</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
                Prove the workflow before expanding it.
              </h2>
              <p className="mt-5 text-lg leading-8 text-pns-text-muted">
                A focused first version uses representative files, known fields, clear review rules,
                and a measurable baseline. That makes accuracy, time saved, and exception handling
                visible before the system grows.
              </p>
              <Link href="/solutions#ai-document-processing" className="mt-6 inline-flex items-center gap-2 font-semibold text-[#0b6575] hover:underline">
                See this service in our solutions overview <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="rounded-3xl bg-[#051226] p-7 text-white sm:p-9">
              <ShieldCheck className="h-9 w-9 text-cyan-300" aria-hidden="true" />
              <h3 className="mt-5 text-2xl font-semibold">Built around review and accountability</h3>
              <ul className="mt-6 space-y-4 text-white/78">
                {[
                  "Human review for exceptions and important decisions",
                  "Validation rules for required fields and expected formats",
                  "Clear handling for low-confidence or unreadable documents",
                  "Document access and retention planned around the workflow",
                  "Audit-friendly records of what was processed and approved",
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <Check className="mt-0.5 h-5 w-5 shrink-0 text-cyan-300" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-20 lg:py-24">
        <Container size="narrow">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.15em] text-[#0b6575]">Common questions</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-pns-text-primary lg:text-5xl">
              Document processing automation FAQ
            </h2>
          </div>
          <div className="mt-10 divide-y divide-black/10 border-y border-black/10">
            {faqs.map((faq) => (
              <article key={faq.question} className="py-6">
                <h3 className="text-xl font-semibold text-pns-text-primary">{faq.question}</h3>
                <p className="mt-3 leading-7 text-pns-text-muted">{faq.answer}</p>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="bg-[#051226] py-20 text-white">
        <Container size="narrow">
          <div className="text-center">
            <h2 className="text-3xl font-semibold tracking-tight lg:text-5xl">
              Find out whether your document workflow is ready to automate.
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-white/75">
              Use the assessment for a quick starting point, or show us one representative document
              and the manual process around it.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Button href="/assessment" size="lg" className="bg-white !text-[#051226] hover:bg-white/90">
                Take the assessment
              </Button>
              <Button
                href="/contact?service=document-processing-automation"
                variant="outline"
                size="lg"
                className="border-white/40 !text-white hover:bg-white/10"
              >
                Contact Pacific North Systems
              </Button>
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}
