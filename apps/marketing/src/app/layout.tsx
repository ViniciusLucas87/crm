import type { Metadata } from "next";
import Script from "next/script";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { siteConfig } from "@/lib/site-config";
import "./globals.css";

const googleAdsId = process.env.NEXT_PUBLIC_GOOGLE_ADS_ID?.trim();
const hasGoogleAdsId = Boolean(googleAdsId && /^AW-\d+$/.test(googleAdsId));
const googleAnalyticsId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID?.trim();
const hasGoogleAnalyticsId = Boolean(
  googleAnalyticsId && /^G-[A-Z0-9]+$/.test(googleAnalyticsId),
);
const googleTagId = hasGoogleAnalyticsId ? googleAnalyticsId : googleAdsId;

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
  alternates: {
    canonical: "/",
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
        {googleTagId ? (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${googleTagId}`}
              strategy="afterInteractive"
            />
            <Script id="google-tag" strategy="afterInteractive">
              {`window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
${hasGoogleAnalyticsId ? `gtag('config', '${googleAnalyticsId}');` : ""}
${hasGoogleAdsId ? `gtag('config', '${googleAdsId}');` : ""}
document.addEventListener('click', function(event) {
  var element = event.target instanceof Element ? event.target.closest('a') : null;
  if (!element) return;
  var href = element.getAttribute('href') || '';
  var eventName = href.indexOf('tel:') === 0 ? 'phone_click' : href.indexOf('mailto:') === 0 ? 'email_click' : href.indexOf('calendly.com') !== -1 ? 'consultation_booking_click' : '';
  if (eventName) gtag('event', eventName, { link_url: href });
});`}
            </Script>
          </>
        ) : null}
        <Header />
        <main className="flex-1" id="main-content">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
