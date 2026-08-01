import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || !process.env.CLERK_SECRET_KEY) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#12343b,_#06131a_45%,_#02070a)] p-6 text-slate-100">
        <div className="max-w-xl rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur">
          <h1 className="text-2xl font-semibold tracking-tight">Authentication configuration required</h1>
          <p className="mt-3 text-sm text-slate-300">Provide the Clerk publishable and secret keys before using the sign-in flow.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#12343b,_#06131a_45%,_#02070a)] p-6">
      <SignIn path="/sign-in" routing="path" forceRedirectUrl="/" signUpUrl="/sign-up" />
    </main>
  );
}