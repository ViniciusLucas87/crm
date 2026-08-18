import type { Metadata } from "next";
import { Container } from "@/components/ui/container";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "Terms of service for Pacific North Systems custom software and automation consulting.",
};

export default function TermsPage() {
  return (
    <main className="pt-28 pb-16 lg:pt-32 lg:pb-20">
      <Container size="narrow">
        <div className="max-w-[720px] mx-auto prose prose-lg">
          <h1>Terms of Service</h1>
          <p className="text-sm text-pns-text-muted">
            Last updated: August 2026
          </p>

          <h2>1. Services</h2>
          <p>
            Pacific North Systems (&ldquo;PNS,&rdquo; &ldquo;we,&rdquo;
            &ldquo;us&rdquo;) provides custom software development, workflow
            automation, and technology consulting services. All engagements are
            governed by a written Statement of Work (SOW) or service agreement
            executed by both parties.
          </p>

          <h2>2. Intellectual Property</h2>
          <p>
            Upon full payment, clients receive ownership of custom code and
            deliverables specified in their SOW. PNS retains ownership of
            pre-existing tools, libraries, and frameworks used in delivery. PNS
            may showcase anonymized project outcomes in its portfolio unless the
            client requests otherwise in writing.
          </p>

          <h2>3. Confidentiality</h2>
          <p>
            Both parties agree to protect confidential information shared during
            the engagement. PNS will not disclose client data, business
            processes, or proprietary information to third parties without prior
            written consent, except as required by law.
          </p>

          <h2>4. Limitation of Liability</h2>
          <p>
            PNS provides services on a best-effort basis. Our liability is
            limited to the fees paid for the specific service giving rise to the
            claim. We are not liable for indirect, incidental, or consequential
            damages.
          </p>

          <h2>5. Payment Terms</h2>
          <p>
            Payment terms are defined in each SOW. Standard terms are net-15
            for invoiced work. Late payments may incur interest at 1.5% per
            month or the maximum rate permitted by law.
          </p>

          <h2>6. Termination</h2>
          <p>
            Either party may terminate an engagement with 30 days&apos; written
            notice. Upon termination, the client pays for all work completed
            through the termination date, and PNS delivers all completed work
            product.
          </p>

          <h2>7. Governing Law</h2>
          <p>
            These terms are governed by the laws of British Columbia, Canada.
            Any disputes shall be resolved in the courts of Victoria, British
            Columbia.
          </p>

          <h2>8. Never Miss Subscription Service</h2>
          <p>
            Never Miss responds to eligible unanswered calls with an automated
            text and records callback information. Customers remain responsible
            for configuring unanswered-call forwarding with their carrier,
            keeping their reply message accurate, obtaining any consent required
            for their use, and monitoring customer follow-up. Never Miss is not
            an emergency service and must not be used for urgent medical, safety,
            or emergency communications.
          </p>
          <p>
            Message delivery and call forwarding depend on telephone carriers
            and third-party networks and cannot be guaranteed. Plan usage limits
            apply. We may pause abusive, unlawful, fraudulent, or unusually high
            traffic to protect customers and the service. Customers may cancel
            through the billing portal. After cancellation, automatic replies
            stop and the customer must remove call forwarding from their carrier.
          </p>

          <h2>9. Contact</h2>
          <p>
            Questions about these terms? Contact us at{" "}
            <Link
              href="mailto:hello@pacificnorthsystems.com"
              className="underline"
            >
              hello@pacificnorthsystems.com
            </Link>
            .
          </p>
        </div>
      </Container>
    </main>
  );
}
