import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function proxyAuthenticatedApi(request: NextRequest, path: string): Promise<NextResponse> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || !process.env.CLERK_SECRET_KEY) {
    return NextResponse.json({ detail: "Authentication is not configured" }, { status: 503 });
  }

  const session = await auth();

  if (!session.userId) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const token = await session.getToken();
  if (!token) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const apiUrl = new URL(`/api/v1${path}`, API_BASE_URL);
  apiUrl.search = request.nextUrl.search;

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  // Preserve the exact request body. Reading uploads as text corrupts multipart
  // files (PDFs, recordings, images) before they reach FastAPI.
  const body = request.method === "GET" || request.method === "HEAD"
    ? undefined
    : await request.arrayBuffer();

  try {
    const response = await fetch(apiUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });
    const payload = await response.text();

    return new NextResponse(payload, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 503 });
  }
}
