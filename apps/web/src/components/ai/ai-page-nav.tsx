"use client";

import Link from "next/link";
import { ArrowLeft, ChevronRight } from "lucide-react";
import type { Route } from "next";

type Props = {
  companyName?: string;
  companyId: string | number;
  pageTitle: string;
};

export function AiPageNav({ companyName, companyId, pageTitle }: Props) {
  return (
    <div className="mb-6 space-y-2">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-slate-500" aria-label="Breadcrumb">
        <Link href="/" className="transition hover:text-slate-300">Home</Link>
        <ChevronRight className="h-3 w-3" />
        <Link href="/companies" className="transition hover:text-slate-300">Companies</Link>
        <ChevronRight className="h-3 w-3" />
        <Link href={`/companies/${companyId}` as Route} className="transition hover:text-slate-300">
          {companyName || `Company #${companyId}`}
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span className="text-slate-300">{pageTitle}</span>
      </nav>

      {/* Back link */}
      <Link
        href={`/companies/${companyId}` as Route}
        className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition hover:text-cyan-300"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to {companyName || "company"}
      </Link>
    </div>
  );
}

export function AiPageError({ message }: { message: string; companyId?: string }) {
  return (
    <div className="space-y-4">
      <Link href="/companies" className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition hover:text-cyan-300">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Companies
      </Link>
      <div className="rounded-2xl border border-red-400/10 bg-red-400/5 p-8 text-center">
        <p className="text-sm text-red-400">{message}</p>
        <div className="mt-4 flex justify-center gap-3">
          <Link href="/companies" className="rounded-xl border border-white/10 px-4 py-2 text-xs text-slate-400 transition hover:border-white/20 hover:text-white">
            Go to Companies
          </Link>
          <Link href="/" className="rounded-xl border border-white/10 px-4 py-2 text-xs text-slate-400 transition hover:border-white/20 hover:text-white">
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
