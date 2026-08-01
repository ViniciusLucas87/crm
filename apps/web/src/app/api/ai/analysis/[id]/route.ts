import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const API = process.env.API_URL ?? "http://api:8000";

async function proxy(path: string) {
  const sesh = await auth(); const token = await sesh.getToken();
  const res = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxy(`/api/v1/ai/analysis/${id}`);
}
