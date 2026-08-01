import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArticleCard } from "@/components/blog";
import { BlogFAQ } from "@/components/blog";
import {
  getArticleBySlug,
  getAllArticles,
  getRelatedArticles,
} from "@/lib/blog";
import { siteConfig } from "@/lib/site-config";
import { renderMarkdown } from "@/lib/markdown";
import { Calendar, Clock, ArrowLeft } from "lucide-react";

interface ArticlePageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  const articles = await getAllArticles();
  return articles.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({
  params,
}: ArticlePageProps): Promise<Metadata> {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);
  if (!article) return {};

  const { frontmatter } = article;
  return {
    title: frontmatter.seoTitle || frontmatter.title,
    description:
      frontmatter.metaDescription ||
      frontmatter.description ||
      frontmatter.excerpt,
    openGraph: {
      type: "article",
      title: frontmatter.seoTitle || frontmatter.title,
      description: frontmatter.metaDescription || frontmatter.excerpt,
      publishedTime: frontmatter.publishedAt,
      modifiedTime: frontmatter.updatedAt,
      authors: [frontmatter.author],
    },
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);

  if (!article) {
    notFound();
  }

  const { frontmatter, content } = article;
  const related = await getRelatedArticles(
    slug,
    frontmatter.relatedArticleSlugs || [],
  );

  return (
    <main>
      {/* Article header */}
      <section className="bg-pns-dark-hero pt-28 pb-16 lg:pt-32 lg:pb-20">
        <Container size="narrow">
          <Link
            href="/blog"
            className="inline-flex items-center gap-2 text-sm text-pns-text-light hover:text-pns-text-soft-white transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Blog
          </Link>

          <div className="flex items-center gap-3 text-xs text-pns-text-light mb-4">
            <Badge
              variant="outline"
              className="!border-white/30 !text-pns-text-light"
            >
              {frontmatter.category}
            </Badge>
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" aria-hidden="true" />
              {new Date(frontmatter.publishedAt).toLocaleDateString("en-CA", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" aria-hidden="true" />
              {frontmatter.readingTime}
            </span>
          </div>

          <h1 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-soft-white leading-tight">
            {frontmatter.title}
          </h1>

          <p className="mt-4 text-pns-text-light leading-relaxed max-w-2xl">
            {frontmatter.excerpt}
          </p>

          <div className="mt-6 flex items-center gap-3 pt-6 border-t border-white/10">
            <div>
              <p className="font-medium text-pns-text-soft-white">
                {frontmatter.author}
              </p>
              <p className="text-sm text-pns-text-footer-muted">
                {frontmatter.authorRole}
              </p>
            </div>
          </div>
        </Container>
      </section>

      {/* Featured image */}
      {frontmatter.featuredImage && (
        <section className="bg-white">
          <Container size="narrow">
            <div className="max-w-[720px] mx-auto -mt-8 relative z-10">
              <Image
                src={frontmatter.featuredImage}
                alt={frontmatter.imageAlt || frontmatter.title}
                width={1440}
                height={810}
                className="w-full rounded-[16px] shadow-lg"
                priority
              />
            </div>
          </Container>
        </section>
      )}

      {/* Article body */}
      <section className="py-12 lg:py-16 bg-white">
        <Container size="narrow">
          <div className="max-w-[720px] mx-auto">
            <div
              className="prose prose-lg max-w-none
                prose-headings:text-pns-text-primary prose-headings:font-bold
                prose-p:text-pns-text-muted prose-p:leading-relaxed
                prose-li:text-pns-text-muted
                prose-strong:text-pns-text-primary
                prose-a:text-pns-text-primary prose-a:underline"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
            />

            {/* Tags */}
            {frontmatter.tags && frontmatter.tags.length > 0 && (
              <div className="mt-10 pt-6 border-t border-pns-text-primary/10">
                <div className="flex flex-wrap gap-2">
                  {frontmatter.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs text-pns-text-muted bg-pns-soft-blue px-3 py-1 rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* FAQ */}
            {frontmatter.faq && <BlogFAQ items={frontmatter.faq} />}

            {/* Article CTA */}
            <div className="mt-12 p-8 rounded-[16px] bg-pns-soft-blue text-center">
              <h2 className="text-xl font-bold text-pns-text-primary">
                Ready to review your workflow?
              </h2>
              <p className="mt-2 text-pns-text-muted">
                Book a free Operations Audit and we will help you identify
                where to start.
              </p>
              <div className="mt-6">
                <Button
                  variant="primary"
                  href={
                    frontmatter.primaryCtaUrl ||
                    siteConfig.contact.calendlyAudit
                  }
                  external
                >
                  {frontmatter.primaryCtaLabel || "Book a free Operations Audit"}
                </Button>
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* Related articles */}
      {related.length > 0 && (
        <section className="py-12 lg:py-16 bg-pns-bg">
          <Container size="narrow">
            <h2 className="text-2xl font-bold text-pns-text-primary mb-8">
              Related articles
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {related.map((r) => (
                <ArticleCard key={r.slug} article={r} />
              ))}
            </div>
          </Container>
        </section>
      )}
    </main>
  );
}
