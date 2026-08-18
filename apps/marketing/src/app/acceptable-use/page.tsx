import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/ui/container";

export const metadata: Metadata = {
  title: "Never Miss Acceptable Use",
  description: "Simple rules that keep Never Miss calling and messaging safe and respectful.",
};

export default function AcceptableUsePage() {
  return <main className="pb-16 pt-28 lg:pb-20 lg:pt-32"><Container size="narrow"><div className="prose prose-lg mx-auto max-w-[720px]">
    <h1>Never Miss Acceptable Use</h1><p className="text-sm text-pns-text-muted">Last updated: August 2026</p>
    <p>Never Miss is designed to reply to people who have just called a business and reasonably expect a response from that business.</p>
    <h2>Allowed use</h2><ul><li>Replying after a genuine unanswered business call</li><li>Identifying the business clearly</li><li>Asking what the caller needs and organizing a callback</li><li>Respecting STOP and other opt-out requests immediately</li></ul>
    <h2>Not allowed</h2><ul><li>Purchased lists, cold-text campaigns, or unsolicited bulk messaging</li><li>Harassment, deception, impersonation, fraud, or unlawful content</li><li>Emergency, medical, crisis, or safety-critical communications</li><li>Attempts to bypass usage limits, opt-outs, security controls, or carrier rules</li><li>Automated replies to short codes, emergency numbers, or clearly automated systems</li></ul>
    <h2>Service protection</h2><p>We may slow, block, or pause suspicious traffic while we investigate. Repeated or serious violations can result in termination. These protections help keep delivery reliable for legitimate businesses.</p>
    <h2>Questions</h2><p>Contact <Link href="mailto:hello@pacificnorthsystems.com">hello@pacificnorthsystems.com</Link>.</p>
  </div></Container></main>;
}
