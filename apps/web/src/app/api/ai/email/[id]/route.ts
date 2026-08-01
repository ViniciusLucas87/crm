import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
const API = process.env.API_URL ?? "http://api:8000";
export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params; const sesh = await auth();
  const qs = req.nextUrl.searchParams.toString();
  const res = await fetch(`${API}/api/v1/ai/email/${id}${qs ? `?${qs}` : ""}`, { headers: { Authorization: `Bearer ${await sesh.getToken()}` } });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}
