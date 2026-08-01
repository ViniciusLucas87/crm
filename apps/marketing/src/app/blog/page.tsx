import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/ui/container";
import { Button } from "@/components/ui/button";
import { ArticleCard } from "@/components/blog";
import { getAllArticles, getFeaturedArticle, getUniqueCategories } from "@/lib/blog";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Business Automation Blog",
  description:
    "Practical guidance on workflow automation, operational efficiency, AI, custom software, and internal tools for Canadian businesses.",
};

export default async function BlogPage() {
  const articles = await getAllArticles();
  const featured = await getFeaturedArticle();
  const categories = getUniqueCategories(articles);

  // Remove featured from main list
  const mainArticles = featured
    ? articles.filter((a) => a.slug !== featured.slug)
    : articles;

  return (
    <main>
      {/* Header */}
      <section className="bg-pns-dark-hero pt-28 pb-16 lg:pt-32 lg:pb-20">
        <Container size="narrow">
          <h1 className="text-[clamp(2rem,4vw,3rem)] font-bold text-pns-text-soft-white">
            Business Automation Blog
          </h1>
          <p className="mt-4 text-pns-text-light leading-relaxed">
            Practical guidance on workflow automation, operational efficiency,
            AI, custom software, and internal tools for Canadian businesses.
          </p>
        </Container>
      </section>

      <Container size="narrow">
        <div className="py-12 lg:py-16">
          {/* Featured article */}
          {featured && (
            <div className="mb-12">
              <p className="text-sm font-medium text-pns-text-muted uppercase tracking-wide mb-4">
                Featured Article
              </p>
              <ArticleCard article={featured} featured />
            </div>
          )}

          {/* Categories */}
          {categories.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-8">
              <span className="text-sm font-medium text-pns-text-primary mr-2">
                Categories:
              </span>
              {categories.map((cat) => (
                <Link
                  key={cat}
                  href={`/blog?category=${encodeURIComponent(cat)}`}
                  className="text-sm text-pns-text-muted hover:text-pns-text-primary border border-pns-text-primary/15 rounded-full px-3 py-1 transition-colors"
                >
                  {cat}
                </Link>
              ))}
            </div>
          )}

          {/* Article grid */}
          {mainArticles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {mainArticles.map((article) => (
                <ArticleCard key={article.slug} article={article} />
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <p className="text-pns-text-muted">
                Articles are on the way. Check back soon for practical
                automation guidance.
              </p>
            </div>
          )}

          {/* CTA */}
          <div className="mt-16 p-8 rounded-[16px] bg-pns-soft-blue text-center">
            <h2 className="text-xl font-bold text-pns-text-primary">
              Ready to identify your biggest time drain?
            </h2>
            <p className="mt-2 text-pns-text-muted">
              Book a free Operations Audit, and we will review your current
              processes together.
            </p>
            <div className="mt-6">
              <Button
                variant="primary"
                href={siteConfig.contact.calendlyAudit}
                external
              >
                Book a 30-minute Operations Audit
              </Button>
            </div>
          </div>
        </div>
      </Container>
    </main>
  );
}
