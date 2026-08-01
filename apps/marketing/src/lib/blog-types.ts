export interface ArticleFrontmatter {
  title: string;
  slug: string;
  description: string;
  excerpt: string;
  author: string;
  authorRole: string;
  publishedAt: string;
  updatedAt: string;
  readingTime: string;
  category: string;
  tags: string[];
  featured: boolean;
  featuredImage?: string;
  imageAlt: string;
  seoTitle?: string;
  metaDescription?: string;
  primaryCtaLabel?: string;
  primaryCtaUrl?: string;
  faq?: FAQItem[];
  relatedArticleSlugs?: string[];
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface Article {
  frontmatter: ArticleFrontmatter;
  content: string;
  slug: string;
}
