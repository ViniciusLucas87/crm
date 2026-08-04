import { clerkMiddleware } from "@clerk/nextjs/server";

export default clerkMiddleware(async (auth, req) => {
  const path = req.nextUrl.pathname;
  if (path.startsWith("/today") || path.startsWith("/audit") || path.startsWith("/operations")) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};