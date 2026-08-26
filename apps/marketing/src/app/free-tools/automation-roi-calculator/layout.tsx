import type { Metadata } from "next";

const url = "https://www.pacificnorthsystems.com/free-tools/automation-roi-calculator";
const description = "Estimate automation benefits, ongoing costs, first-year ROI, and payback time using transparent business assumptions.";
export const metadata: Metadata = { title: "Automation ROI Calculator | Pacific North Systems", description, alternates: { canonical: url }, openGraph: { title: "Automation ROI Calculator", description, url } };

export default function Layout({ children }: { children: React.ReactNode }) {
  const jsonLd = { "@context": "https://schema.org", "@type": "WebApplication", name: "Automation ROI Calculator", applicationCategory: "BusinessApplication", operatingSystem: "Any", description, url, offers: { "@type": "Offer", price: "0", priceCurrency: "CAD" } };
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />{children}</>;
}
