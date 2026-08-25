import type { Metadata } from "next";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { siteConfig } from "@/lib/site-config";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: `${siteConfig.name} | Custom Software for Teams with Complex Operations`,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  metadataBase: new URL(siteConfig.url),
  icons: {
    icon: "/images/favicon.png",
  },
  openGraph: {
    type: "website",
    locale: "en_CA",
    url: siteConfig.url,
    siteName: siteConfig.name,
    title: `${siteConfig.name} | Custom Software for Teams with Complex Operations`,
    description: siteConfig.description,
    images: [
      {
        url: "/images/social.png",
        width: 1200,
        height: 630,
        alt: `${siteConfig.name}: Custom software and automation for teams with complex operations`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: `${siteConfig.name} | Custom Software for Teams with Complex Operations`,
    description: siteConfig.description,
    images: ["/images/social.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${siteConfig.url}/#organization`,
        name: siteConfig.name,
        url: siteConfig.url,
        email: siteConfig.contact.email,
        telephone: siteConfig.contact.phone,
        description: siteConfig.description,
        address: {
          "@type": "PostalAddress",
          streetAddress: "2485 West Broadway",
          addressLocality: "Vancouver",
          addressRegion: "BC",
          postalCode: "V6K 2E8",
          addressCountry: "CA",
        },
        sameAs: [],
      },
      {
        "@type": "WebSite",
        "@id": `${siteConfig.url}/#website`,
        url: siteConfig.url,
        name: siteConfig.name,
        description: siteConfig.description,
        publisher: { "@id": `${siteConfig.url}/#organization` },
      },
    ],
  };

  return (
    <html lang="en-CA" className="scroll-smooth">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-screen flex flex-col overflow-x-clip antialiased">
        <Header />
        <main className="flex-1" id="main-content">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
