import Link from "next/link";
import { Shell } from "@/components/dashboard/shell";
import { Search, Building2, Home, Sparkles, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <Shell>
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <div className="mb-6 rounded-2xl bg-white/5 p-4">
          <Search className="h-10 w-10 text-slate-600" />
        </div>
        <h1 className="text-2xl font-semibold text-white">Page not found</h1>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          The page you&apos;re looking for doesn&apos;t exist or may have been moved.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link href="/" className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-300 transition hover:border-white/20 hover:text-white">
            <Home className="h-4 w-4" />Dashboard
          </Link>
          <Link href="/companies" className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-300 transition hover:border-white/20 hover:text-white">
            <Building2 className="h-4 w-4" />Companies
          </Link>
          <Link href="/ai/daily-brief" className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-300 transition hover:border-white/20 hover:text-white">
            <Sparkles className="h-4 w-4" />AI Daily Brief
          </Link>
          <Link href="/" className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-300 transition hover:border-white/20 hover:text-white">
            <ArrowLeft className="h-4 w-4" />Back to Home
          </Link>
        </div>
      </div>
    </Shell>
  );
}
