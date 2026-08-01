import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
const API = process.env.API_URL ?? "http://api:8000";
export async function GET() {
  const sesh = await auth();
  const res = await fetch(`${API}/api/v1/mcp/tools`, { headers: { Authorization: `Bearer ${await sesh.getToken()}` } });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}
