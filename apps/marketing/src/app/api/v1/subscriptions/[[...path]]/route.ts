import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const API_BASE = (
  process.env.INTERNAL_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://api.pacificnorthsystems.com"
).replace(/\/$/, "");

function upstreamUrl(path: string[] | undefined) {
  const safePath = path || [];
  if (!new Set(["onboarding", "manage"]).has(safePath[0])) return null;
  return `${API_BASE}/api/v1/subscriptions/${safePath.map(encodeURIComponent).join("/")}`;
}

async function proxy(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  const { path } = await context.params;
  const url = upstreamUrl(path);
  if (!url) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const response = await fetch(url, {
    method: request.method,
    headers: { "Content-Type": request.headers.get("content-type") || "application/json" },
    body: request.method === "GET" ? undefined : await request.text(),
    cache: "no-store",
  });
  return new NextResponse(await response.text(), {
    status: response.status,
    headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
  });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
