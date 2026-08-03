import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight, Calculator } from "lucide-react";
import { guides } from "@/lib/guides-data";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const guide = guides[slug];
  if (!guide) return { title: "Not Found" };

  return {
    title: `${guide.title} | Pacific North Systems`,
    description: guide.description,
    alternates: { canonical: `https://pacificnorthsystems.com/business-guides/${slug}` },
    openGraph: { title: guide.title, description: guide.description },
  };
}

export async function generateStaticParams() {
  return Object.keys(guides).map((slug) => ({ slug }));
}

export default async function GuidePage({ params }: Props) {
  const { slug } = await params;
  const guide = guides[slug];
  if (!guide) notFound();

  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: guide.title,
    description: guide.description,
    author: { "@type": "Organization", name: "Pacific North Systems" },
    publisher: { "@type": "Organization", name: "Pacific North Systems" },
  };
  const faqJsonLd = guide.faq
    ? {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: guide.faq.map((item) => ({
          "@type": "Question",
          name: item.question,
          acceptedAnswer: { "@type": "Answer", text: item.answer },
        })),
      }
    : null;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />
      {faqJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
        />
      )}

      <Section variant="dark">
        <Container>
          <div className="max-w-[920px] mx-auto py-8">
            <Link
              href="/business-guides"
              className="inline-flex items-center gap-1 text-[14px] text-pns-text-light hover:text-white transition-colors mb-4"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              All guides
            </Link>
            <div className="flex items-center gap-3 mb-4">
              <Badge>{guide.category}</Badge>
              <span className="text-[13px] text-pns-text-light">
                {guide.readTime} read
              </span>
            </div>
            <h1 className="font-heading text-[clamp(1.5rem,3.5vw,2.25rem)] font-bold text-white mb-3">
              {guide.title}
            </h1>
            <p className="text-pns-text-light text-[16px] leading-relaxed max-w-2xl">
              {guide.description}
            </p>
          </div>
        </Container>
      </Section>

      <Section>
        <Container className="max-w-[920px]">
          <article className="prose-custom">
            {guide.content.map((section, i) => (
              <div key={i} className="mb-8">
                <h2 className="font-heading font-semibold text-[20px] text-pns-text-primary mb-3">
                  {section.heading}
                </h2>
                <p className="text-[15px] text-pns-text-muted leading-relaxed">
                  {section.body}
                </p>
              </div>
            ))}
          </article>

          {guide.faq && guide.faq.length > 0 && (
            <section className="mt-10 pt-8 border-t border-pns-assessment-input-border">
              <h2 className="font-heading font-semibold text-[22px] text-pns-text-primary mb-5">
                Frequently asked questions
              </h2>
              <div className="space-y-3">
                {guide.faq.map((item) => (
                  <details
                    key={item.question}
                    className="rounded-[14px] border border-pns-assessment-input-border bg-white p-5"
                  >
                    <summary className="cursor-pointer font-semibold text-pns-text-primary">
                      {item.question}
                    </summary>
                    <p className="mt-3 text-[15px] leading-relaxed text-pns-text-muted">
                      {item.answer}
                    </p>
                  </details>
                ))}
              </div>
            </section>
          )}

          {/* Linked tool CTA */}
          {guide.linkedTool && (
            <Card className="mt-10 p-6 bg-pns-soft-blue border-pns-soft-blue" variant="elevated">
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <div className="w-10 h-10 rounded-[10px] bg-white flex items-center justify-center flex-shrink-0">
                  <Calculator className="w-5 h-5 text-[#051226]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-heading font-semibold text-[16px] text-pns-text-primary mb-1">
                    Try our free {guide.linkedTool.label}
                  </h3>
                  <p className="text-[14px] text-pns-text-muted">
                    No signup required. Get personalized estimates in under two
                    minutes.
                  </p>
                </div>
                <Link href={guide.linkedTool.href}>
                  <Button>
                    Open calculator
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </Card>
          )}

          {/* Related guides */}
          {guide.linkedGuides && guide.linkedGuides.length > 0 && (
            <div className="mt-10 pt-8 border-t border-pns-assessment-input-border">
              <h3 className="font-heading font-semibold text-[18px] text-pns-text-primary mb-4">
                Related guides
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {guide.linkedGuides.map((linkedSlug) => {
                  const linked = guides[linkedSlug];
                  if (!linked) return null;
                  return (
                    <Link key={linkedSlug} href={`/business-guides/${linkedSlug}`}>
                      <Card className="h-full hover:shadow-md transition-shadow p-4" variant="elevated">
                        <span className="text-[12px] font-medium bg-pns-soft-blue text-pns-text-primary px-2 py-0.5 rounded-full">
                          {linked.category}
                        </span>
                        <h4 className="font-heading font-semibold text-[15px] text-pns-text-primary mt-2 mb-1">
                          {linked.title}
                        </h4>
                        <p className="text-[13px] text-pns-text-muted">
                          {linked.readTime} read
                        </p>
                      </Card>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </Container>
      </Section>
    </>
  );
}
