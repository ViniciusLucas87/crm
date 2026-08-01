export default function AuthConfigurationPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#12343b,_#06131a_45%,_#02070a)] p-6 text-slate-100">
      <div className="max-w-xl rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur">
        <h1 className="text-2xl font-semibold tracking-tight">Authentication configuration required</h1>
        <p className="mt-3 text-sm text-slate-300">
          Clerk is enabled in this application, but the required environment variables are not configured yet.
        </p>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-300">
          <li>Set <code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> in the web environment.</li>
          <li>Set <code>CLERK_SECRET_KEY</code> in the web environment.</li>
          <li>Set <code>CLERK_ISSUER</code> and <code>CLERK_JWKS_URL</code> in the API environment.</li>
        </ul>
      </div>
    </main>
  );
}