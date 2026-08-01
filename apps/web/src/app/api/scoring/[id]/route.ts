import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

export async function POST(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const sesh = await auth();
  const token = await sesh.getToken();
  const { id } = await params;
  const res = await fetch(`${process.env.API_URL ?? "http://api:8000"}/api/v1/scoring/${id}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return NextResponse.json({ error: await res.text() }, { status: res.status });
  return NextResponse.json(await res.json());
}
