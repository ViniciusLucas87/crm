import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
const API = process.env.API_URL ?? "http://api:8000";
export async function POST(_r: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params; const sesh = await auth();
  const res = await fetch(`${API}/api/v1/ai/call/debrief/${id}`, { method: "POST", headers: { Authorization: `Bearer ${await sesh.getToken()}` } });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}
