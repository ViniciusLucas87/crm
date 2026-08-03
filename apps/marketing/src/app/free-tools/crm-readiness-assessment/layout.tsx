import type { Metadata } from "next";

const url = "https://pacificnorthsystems.com/free-tools/crm-readiness-assessment";
const description = "Check whether your business is ready for a CRM and receive practical next steps based on your current sales process.";
export const metadata: Metadata = { title: "CRM Readiness Assessment | Pacific North Systems", description, alternates: { canonical: url }, openGraph: { title: "CRM Readiness Assessment", description, url } };

export default function Layout({ children }: { children: React.ReactNode }) {
  const jsonLd = { "@context": "https://schema.org", "@type": "WebApplication", name: "CRM Readiness Assessment", applicationCategory: "BusinessApplication", operatingSystem: "Any", description, url, offers: { "@type": "Offer", price: "0", priceCurrency: "CAD" } };
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />{children}</>;
}
