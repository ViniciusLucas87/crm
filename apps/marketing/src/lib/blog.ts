import fs from "fs";
import path from "path";
import type { Article, ArticleFrontmatter } from "./blog-types";

const articlesDir = path.join(process.cwd(), "content", "articles");

function parseFrontmatter(raw: string): {
  frontmatter: ArticleFrontmatter;
  content: string;
} {
  // Strip BOM if present
  const clean = raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw;

  // Split on --- delimiters
  const parts = clean.split(/^---\s*$/m);
  if (parts.length < 3) {
    throw new Error("Invalid frontmatter format");
  }

  const frontmatterStr = parts[1];
  const content = parts.slice(2).join("---").trim();

  const frontmatter: Record<string, unknown> = {};

  for (const line of frontmatterStr.split(/\r?\n/)) {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;

    const key = line.slice(0, colonIdx).trim();
    if (!key || key.startsWith("#")) continue;

    let rawValue = line.slice(colonIdx + 1).trim();

    // Remove surrounding quotes
    rawValue = rawValue.replace(/^["']|["']$/g, "");

    if (rawValue.startsWith("[") && rawValue.endsWith("]")) {
      frontmatter[key] = rawValue
        .slice(1, -1)
        .split(",")
        .map((s: string) => s.trim().replace(/^["']|["']$/g, ""))
        .filter(Boolean);
    } else if (rawValue === "true" || rawValue === "false") {
      frontmatter[key] = rawValue === "true";
    } else {
      frontmatter[key] = rawValue;
    }
  }

  return {
    frontmatter: frontmatter as unknown as ArticleFrontmatter,
    content,
  };
}

export async function getAllArticles(): Promise<Article[]> {
  if (!fs.existsSync(articlesDir)) {
    return [];
  }

  const files = fs
    .readdirSync(articlesDir)
    .filter((f) => f.endsWith(".md") || f.endsWith(".mdx"));

  const articles = files.map((file) => {
    const raw = fs.readFileSync(path.join(articlesDir, file), "utf-8");
    const { frontmatter, content } = parseFrontmatter(raw);
    const slug = frontmatter.slug || file.replace(/\.mdx?$/, "");
    return { frontmatter, content, slug };
  });

  return articles.sort(
    (a, b) =>
      new Date(b.frontmatter.publishedAt).getTime() -
      new Date(a.frontmatter.publishedAt).getTime(),
  );
}

export async function getArticleBySlug(
  slug: string,
): Promise<Article | null> {
  const articles = await getAllArticles();
  return articles.find((a) => a.slug === slug) ?? null;
}

export async function getFeaturedArticle(): Promise<Article | null> {
  const articles = await getAllArticles();
  return articles.find((a) => a.frontmatter.featured) ?? articles[0] ?? null;
}

export async function getRelatedArticles(
  currentSlug: string,
  relatedSlugs: string[],
): Promise<Article[]> {
  const articles = await getAllArticles();
  if (relatedSlugs.length > 0) {
    return articles.filter((a) => relatedSlugs.includes(a.slug));
  }
  // Fallback: return recent articles in the same category
  const current = articles.find((a) => a.slug === currentSlug);
  if (!current) return [];
  return articles
    .filter(
      (a) =>
        a.slug !== currentSlug &&
        a.frontmatter.category === current.frontmatter.category,
    )
    .slice(0, 3);
}

export function getUniqueCategories(articles: Article[]): string[] {
  return [...new Set(articles.map((a) => a.frontmatter.category).filter(Boolean))].sort();
}
