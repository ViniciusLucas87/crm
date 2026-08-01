import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
const API = process.env.API_URL ?? "http://api:8000";

async function proxy(method: string, path: string, body?: unknown) {
  const sesh = await auth();
  const headers: Record<string, string> = { Authorization: `Bearer ${await sesh.getToken()}` };
  if (body) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ agent: string }> }) {
  const { agent } = await params;
  const url = new URL(req.url);
  if (url.pathname.endsWith("/execute")) return proxy("POST", `/api/v1/agents/${agent}/execute`, await req.json());
  return NextResponse.json({ error: "Unknown agent endpoint" }, { status: 404 });
}

export async function GET(_req: NextRequest, { params }: { params: Promise<{ agent: string }> }) {
  const { agent } = await params;
  return proxy("GET", `/api/v1/agents/${agent}`);
}
