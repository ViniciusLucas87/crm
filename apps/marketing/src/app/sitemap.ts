import type { MetadataRoute } from "next";
import { getAllArticles } from "@/lib/blog";
import { guides } from "@/lib/guides-data";

const BASE_URL = "https://pacificnorthsystems.com";
// Stable dates: update when content is materially revised
const SITE_LAUNCH = new Date("2026-06-01");
const TOOLS_ADDED = new Date("2026-08-03");
const GUIDES_PUBLISHED = new Date("2026-08-03");

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const articles = await getAllArticles();
  // Use article frontmatter dates for accurate lastModified
  const articleDates = new Map(
    articles.map((a) => [a.slug, new Date(a.frontmatter.updatedAt || a.frontmatter.publishedAt)])
  );

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: BASE_URL, lastModified: SITE_LAUNCH, changeFrequency: "weekly", priority: 1.0 },
    { url: `${BASE_URL}/solutions`, lastModified: SITE_LAUNCH, changeFrequency: "monthly", priority: 0.9 },
    { url: `${BASE_URL}/free-tools`, lastModified: TOOLS_ADDED, changeFrequency: "weekly", priority: 0.9 },
    { url: `${BASE_URL}/free-tools/manual-work-cost-calculator`, lastModified: TOOLS_ADDED, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/free-tools/automation-roi-calculator`, lastModified: TOOLS_ADDED, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/free-tools/crm-readiness-assessment`, lastModified: TOOLS_ADDED, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/business-guides`, lastModified: GUIDES_PUBLISHED, changeFrequency: "weekly", priority: 0.8 },
    { url: `${BASE_URL}/assessment`, lastModified: SITE_LAUNCH, changeFrequency: "weekly", priority: 1.0 },
    { url: `${BASE_URL}/blog`, lastModified: articles.length > 0 ? articleDates.values().next().value ?? SITE_LAUNCH : SITE_LAUNCH, changeFrequency: "weekly", priority: 0.8 },
    { url: `${BASE_URL}/contact`, lastModified: SITE_LAUNCH, changeFrequency: "monthly", priority: 0.6 },
    { url: `${BASE_URL}/privacy`, lastModified: SITE_LAUNCH, changeFrequency: "yearly", priority: 0.3 },
    { url: `${BASE_URL}/terms`, lastModified: SITE_LAUNCH, changeFrequency: "yearly", priority: 0.3 },
    { url: `${BASE_URL}/research`, lastModified: TOOLS_ADDED, changeFrequency: "monthly", priority: 0.7 },
    { url: `${BASE_URL}/research/manual-work-cost-benchmark-2026`, lastModified: TOOLS_ADDED, changeFrequency: "monthly", priority: 0.7 },
    { url: `${BASE_URL}/methodology`, lastModified: TOOLS_ADDED, changeFrequency: "monthly", priority: 0.5 },
  ];

  const guideRoutes: MetadataRoute.Sitemap = Object.keys(guides).map((slug) => ({
    url: `${BASE_URL}/business-guides/${slug}`,
    lastModified: GUIDES_PUBLISHED,
    changeFrequency: "monthly" as const,
    priority: 0.7,
  }));

  const articleRoutes: MetadataRoute.Sitemap = articles.map((article) => ({
    url: `${BASE_URL}/blog/${article.slug}`,
    lastModified: articleDates.get(article.slug) ?? SITE_LAUNCH,
    changeFrequency: "monthly" as const,
    priority: 0.7,
  }));

  return [...staticRoutes, ...guideRoutes, ...articleRoutes];
}
