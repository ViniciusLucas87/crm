import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const API = process.env.API_URL ?? "http://api:8000";

export async function GET(req: NextRequest) {
  const sesh = await auth(); const token = await sesh.getToken();
  const qs = req.nextUrl.searchParams.toString();
  const res = await fetch(`${API}/api/v1/ai/brief${qs ? `?${qs}` : ""}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}
