import type { Metadata } from "next";

const url = "https://pacificnorthsystems.com/free-tools/manual-work-cost-calculator";
const description = "Estimate the annual time and labour cost of repetitive manual work in your business, with transparent assumptions and no signup required.";
export const metadata: Metadata = { title: "Manual Work Cost Calculator | Pacific North Systems", description, alternates: { canonical: url }, openGraph: { title: "Manual Work Cost Calculator", description, url } };

export default function Layout({ children }: { children: React.ReactNode }) {
  const jsonLd = { "@context": "https://schema.org", "@type": "WebApplication", name: "Manual Work Cost Calculator", applicationCategory: "BusinessApplication", operatingSystem: "Any", description, url, offers: { "@type": "Offer", price: "0", priceCurrency: "CAD" } };
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />{children}</>;
}
