export const siteConfig = {
  name: "Pacific North Systems",
  tagline: "Custom software and automation for businesses worldwide.",
  description:
    "Pacific North Systems builds custom software, workflow automation, dashboards, field tools, and AI powered systems for businesses worldwide.",
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
      { label: "Never Miss", href: "/never-miss" },
      { label: "Services", href: "/solutions" },
      { label: "Work", href: "/work" },
      { label: "About", href: "/about" },
      { label: "Resources", href: "/resources" },
      { label: "Contact", href: "/contact" },
    ],
    cta: {
      label: "Book a Consultation",
      href: "https://calendly.com/vinidias-pacificnorthsystems-operations-audit/30min",
    },
  },
  footer: {
    navigation: [
      { label: "Never Miss", href: "/never-miss" },
      { label: "About", href: "/about" },
      { label: "Our Work", href: "/work" },
      { label: "How We Work", href: "/process" },
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
    resources: [
      { label: "Resource Library", href: "/resources" },
      { label: "Free Tools", href: "/free-tools" },
      { label: "Business Guides", href: "/business-guides" },
      { label: "Research", href: "/research" },
      { label: "Blog", href: "/blog" },
      { label: "Operations Assessment", href: "/assessment" },
    ],
    legal: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
      { label: "Acceptable Use", href: "/acceptable-use" },
    ],
  },
} as const;
