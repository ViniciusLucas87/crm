import Link from "next/link";
import Image from "next/image";
import type { Article } from "@/lib/blog-types";
import { Badge } from "@/components/ui/badge";
import { Clock, Calendar } from "lucide-react";

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-CA", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

interface ArticleCardProps {
  article: Article;
  featured?: boolean;
}

export function ArticleCard({ article, featured = false }: ArticleCardProps) {
  const { frontmatter, slug } = article;

  return (
    <article
      className={`group rounded-[16px] bg-white border border-pns-text-primary/8 overflow-hidden transition-shadow hover:shadow-md ${
        featured ? "lg:grid lg:grid-cols-2" : ""
      }`}
    >
      {/* Image */}
      <div className={`aspect-[16/9] bg-pns-soft-blue flex items-center justify-center overflow-hidden ${featured ? "" : ""}`}>
        {frontmatter.featuredImage ? (
          <Image
            src={frontmatter.featuredImage}
            alt={frontmatter.imageAlt || frontmatter.title}
            width={800}
            height={450}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-pns-text-muted text-sm">
            {frontmatter.imageAlt || "Article image"}
          </span>
        )}
      </div>

      <div className="p-6 flex flex-col">
        <div className="flex items-center gap-3 text-xs text-pns-text-muted mb-3">
          <Badge variant="outline">{frontmatter.category}</Badge>
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" aria-hidden="true" />
            {formatDate(frontmatter.publishedAt)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" aria-hidden="true" />
            {frontmatter.readingTime}
          </span>
        </div>

        <Link href={`/blog/${slug}`} className="group-hover:underline">
          <h2
            className={`font-bold text-pns-text-primary ${
              featured ? "text-xl lg:text-2xl" : "text-lg"
            }`}
          >
            {frontmatter.title}
          </h2>
        </Link>

        <p className="mt-2 text-sm text-pns-text-muted leading-relaxed flex-1">
          {frontmatter.excerpt}
        </p>

        <div className="mt-4 pt-4 border-t border-pns-text-primary/10 flex items-center gap-2">
          <span className="text-sm font-medium text-pns-text-primary">
            {frontmatter.author}
          </span>
          <span className="text-xs text-pns-text-muted">
            {frontmatter.authorRole}
          </span>
        </div>
      </div>
    </article>
  );
}
