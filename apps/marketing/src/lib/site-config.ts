export const siteConfig = {
  name: "Pacific North Systems",
  tagline: "Custom software and automation for operations-heavy teams in Metro Vancouver.",
  description:
    "Pacific North Systems builds custom software, workflow automation, dashboards, field tools, and AI-enabled systems for operations-heavy companies across Vancouver and British Columbia.",
  url: "https://pacificnorthsystems.com",
  contact: {
    email: "hello@pacificnorthsystems.com",
    phone: "+1-604-225-1745",
    location: "Kitsilano - Vancouver, BC",
    calendlyAudit: "https://calendly.com/vinidias-pacificnorthsystems-operations-audit/30min",
  },
  social: {
    // Add social links when available
  },
  nav: {
    primary: [
      { label: "Home", href: "/" },
      { label: "Solutions", href: "/solutions" },
      { label: "Assessment", href: "/assessment" },
      { label: "Blog", href: "/blog" },
    ],
    cta: {
      label: "Take the Assessment",
      href: "/assessment",
    },
  },
  footer: {
    navigation: [
      { label: "Home", href: "/" },
      { label: "Solutions", href: "/solutions" },
      { label: "Demo Systems", href: "/#demo-systems" },
      { label: "Process", href: "/#process" },
      { label: "About", href: "/#about" },
      { label: "Contact", href: "/contact" },
    ],
    solutions: [
      { label: "Custom Applications", href: "/solutions#custom-business-software" },
      { label: "Workflow Automation", href: "/solutions#workflow-automation" },
      { label: "Dashboards & Reporting", href: "/solutions#business-dashboards" },
      { label: "AI Document Tools", href: "/solutions#ai-document-processing" },
      { label: "Integrations", href: "/solutions#system-integrations" },
      { label: "Support & Maintenance", href: "/solutions#operational-it-support" },
    ],
    legal: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
    ],
  },
} as const;
