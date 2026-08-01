/** @type {import('next').NextConfig} */
const nextConfig = {
  async redirects() {
    return [
      {
        source: "/solutions/workflow-automation",
        destination: "/solutions#workflow-automation",
        permanent: true,
      },
      {
        source: "/solutions/custom-software",
        destination: "/solutions#custom-business-software",
        permanent: true,
      },
      {
        source: "/solutions/ai-document-processing",
        destination: "/solutions#ai-document-processing",
        permanent: true,
      },
      {
        source: "/solutions/business-dashboards",
        destination: "/solutions#business-dashboards",
        permanent: true,
      },
      {
        source: "/solutions/integrations",
        destination: "/solutions#system-integrations",
        permanent: true,
      },
      {
        source: "/solutions/inspection-software",
        destination: "/solutions#inspection-software",
        permanent: true,
      },
      {
        source: "/solutions/internal-tools",
        destination: "/solutions#internal-tools",
        permanent: true,
      },
      {
        source: "/solutions/crm-development",
        destination: "/solutions#crm-development",
        permanent: true,
      },
      {
        source: "/solutions/reporting-systems",
        destination: "/solutions#reporting-systems",
        permanent: true,
      },
      {
        source: "/sitemap.xml",
        destination: "/api/sitemap",
        permanent: false,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
