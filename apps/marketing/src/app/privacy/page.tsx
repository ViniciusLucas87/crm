import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Pacific North Systems privacy policy , how we collect, use, and protect your information.",
};

export default function PrivacyPage() {
  return (
    <main className="pt-28 pb-16 lg:pt-32 lg:pb-20">
      <Container size="narrow">
        <div className="max-w-[720px] mx-auto">
          <h1 className="text-[clamp(1.75rem,4vw,2.5rem)] font-bold text-pns-text-primary">
            Privacy Policy
          </h1>
          <p className="mt-2 text-sm text-pns-text-muted">
            Last updated: July 2026
          </p>

          <p className="mt-8 leading-relaxed text-pns-text-muted">
            Pacific North Systems (&ldquo;PNS,&rdquo; &ldquo;we,&rdquo;
            &ldquo;us&rdquo;) is committed to protecting your privacy. This
            policy explains how we collect, use, and safeguard information
            when you visit our website or use our services.
          </p>

          <div className="mt-10 space-y-10 text-pns-text-muted leading-relaxed">
            <Section title="Information We Collect">
              <p>
                Pacific North Systems (&quot;we,&quot; &quot;our,&quot; or
                &quot;us&quot;) collects information you voluntarily provide
                when you:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>Book an Operations Audit through our Calendly integration</li>
                <li>Complete the Business Automation Assessment</li>
                <li>Contact us via email at {siteConfig.contact.email}</li>
                <li>Call us at {siteConfig.contact.phone}</li>
                <li>Purchase, activate, or use Never Miss</li>
              </ul>
              <p className="mt-3">
                This may include your name, email address, phone number, company
                name, industry, and the operational information you choose to
                share.
              </p>
            </Section>

            <Section title="Never Miss Call and Message Data">
              <p>
                When a customer uses Never Miss, we process the customer&apos;s
                business settings and limited call and message records needed to
                detect an unanswered call, send the configured reply, organize a
                callback, prevent abuse, and provide service history. This can
                include telephone numbers, timestamps, delivery status, message
                content, opt-out status, and technical event identifiers.
              </p>
              <p className="mt-3">
                We use Stripe for billing, Telnyx for telephone and messaging
                infrastructure, Resend for service email, and our hosting and
                database providers to operate the product. We do not sell this
                information. Customers may request access or deletion, subject
                to legal, fraud-prevention, billing, and operational retention
                requirements.
              </p>
            </Section>

            <Section title="Assessment Data">
              <p>
                Our Business Automation Assessment collects information about
                your operational processes, employee counts, estimated hours,
                and wage data to calculate directional automation opportunity
                estimates. Assessment progress is saved in your browser&apos;s
                session storage and is not transmitted to our servers unless you
                explicitly consent to submit your results.
              </p>
              <p className="mt-3">
                Assessment data stored in session storage is cleared when you
                close your browser tab. We do not retain assessment data on our
                servers without your explicit consent.
              </p>
            </Section>

            <Section title="Analytics and Cookies">
              <p>
                We may use privacy-focused analytics to understand how visitors
                interact with our website. Any analytics implementation will
                respect Do Not Track signals and minimize data collection. We
                will update this policy when analytics are configured.
              </p>
            </Section>

            <Section title="How We Use Your Information">
              <p>We use the information you provide to:</p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>Respond to your inquiries and schedule consultations</li>
                <li>Prepare for Operations Audits and workflow discussions</li>
                <li>Provide the services you have requested</li>
                <li>Improve our website and assessment tools</li>
                <li>Communicate about our services, with your consent</li>
              </ul>
            </Section>

            <Section title="Information Sharing">
              <p>
                We do not sell, rent, or trade your personal information. We may
                share information with trusted third-party service providers who
                assist us in operating our website and conducting our business
                (such as Calendly for scheduling), subject to confidentiality
                agreements. We may also disclose information when required by
                law.
              </p>
            </Section>

            <Section title="Data Retention">
              <p>
                We retain personal information only as long as necessary to
                fulfill the purposes for which it was collected, or as required
                by applicable law. Assessment data in your browser session
                storage is temporary and cleared when your session ends.
              </p>
            </Section>

            <Section title="Third-Party Services">
              <p>Our website uses the following third-party services:</p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>
                  <strong>Calendly</strong> , for scheduling Operations Audits.
                  Subject to Calendly&apos;s privacy policy.
                </li>
                <li>
                  <strong>Vercel</strong> , for website hosting. Subject to
                  Vercel&apos;s privacy policy.
                </li>
              </ul>
            </Section>

            <Section title="Your Rights">
              <p>
                You have the right to access, correct, or delete your personal
                information. You may also withdraw consent for marketing
                communications at any time. To exercise these rights, contact us
                at {siteConfig.contact.email}.
              </p>
            </Section>

            <Section title="Marketing Communications">
              <p>
                We will only send you marketing communications if you have
                explicitly consented. You may unsubscribe at any time by
                contacting us or using the unsubscribe link in any marketing
                email.
              </p>
            </Section>

            <Section title="Contact Us">
              <p>
                If you have questions about this privacy policy or our data
                practices, please contact us:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>
                  Email:{" "}
                  <a
                    href={`mailto:${siteConfig.contact.email}`}
                    className="text-pns-text-primary underline"
                  >
                    {siteConfig.contact.email}
                  </a>
                </li>
                <li>Phone: {siteConfig.contact.phone}</li>
                <li>Mailing address: {siteConfig.contact.mailingAddress}</li>
              </ul>
            </Section>

            <Section title="Updates to This Policy">
              <p>
                We may update this privacy policy from time to time. Changes
                will be posted on this page with an updated revision date.
              </p>
            </Section>
          </div>
        </div>
      </Container>
    </main>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="text-xl font-bold text-pns-text-primary mb-3">{title}</h2>
      <div className="text-sm text-pns-text-muted space-y-3">{children}</div>
    </section>
  );
}
