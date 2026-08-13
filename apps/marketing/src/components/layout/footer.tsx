import Link from "next/link";
import { Container } from "@/components/ui/container";
import { siteConfig } from "@/lib/site-config";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#061426] text-pns-text-light" role="contentinfo">
      <Container>
        <div className="py-16 lg:py-20">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
            {/* Brand */}
            <div className="lg:col-span-1">
              <Link
                href="/"
                className="text-lg font-bold text-white tracking-tight"
              >
                Pacific North
                <span className="font-normal opacity-60">Systems</span>
              </Link>
              <p className="mt-3 text-sm text-pns-text-footer-muted leading-relaxed">
                {siteConfig.tagline}
              </p>
            </div>

            {/* Navigation */}
            <div>
              <h4 className="text-sm font-semibold text-pns-text-soft-white mb-4">
                Company
              </h4>
              <ul className="space-y-2.5">
                {siteConfig.footer.navigation.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-pns-text-footer-muted hover:text-pns-text-soft-white transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-pns-text-soft-white mb-4">
                Resources
              </h4>
              <ul className="space-y-2.5">
                {siteConfig.footer.resources.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-pns-text-footer-muted hover:text-pns-text-soft-white transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Solutions */}
            <div>
              <h4 className="text-sm font-semibold text-pns-text-soft-white mb-4">
                Solutions
              </h4>
              <ul className="space-y-2.5">
                {siteConfig.footer.solutions.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-pns-text-footer-muted hover:text-pns-text-soft-white transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="text-sm font-semibold text-pns-text-soft-white mb-4">
                Contact
              </h4>
              <ul className="space-y-2.5">
                <li className="text-sm text-pns-text-footer-muted">
                  {siteConfig.contact.location}
                </li>
                <li>
                  <a
                    href={`mailto:${siteConfig.contact.email}`}
                    className="text-sm text-pns-text-footer-muted hover:text-pns-text-soft-white transition-colors"
                  >
                    {siteConfig.contact.email}
                  </a>
                </li>
                <li>
                  <a
                    href={siteConfig.contact.calendlyAudit}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-pns-text-footer-muted hover:text-pns-text-soft-white transition-colors"
                  >
                    Book a Call
                  </a>
                </li>
                <li className="text-sm text-pns-text-footer-muted">
                  {siteConfig.contact.phone}
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-pns-text-footer-muted">
              &copy; {currentYear} Pacific North Systems. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              {siteConfig.footer.legal.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="text-sm text-pns-text-footer-muted hover:text-pns-text-soft-white transition-colors"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </Container>
    </footer>
  );
}
