import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
const API = process.env.API_URL ?? "http://api:8000";
export async function POST(req: NextRequest) {
  const sesh = await auth();
  const body = await req.json();
  const res = await fetch(`${API}/api/v1/mcp/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${await sesh.getToken()}` },
    body: JSON.stringify(body),
  });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}
