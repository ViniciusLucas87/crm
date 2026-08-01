import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type RouteContext = { params: Promise<{ path?: string[] }> };

export async function GET(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const subPath = path?.length ? `/${path.join("/")}` : "";
  return proxyAuthenticatedApi(request, `/transcription${subPath}`);
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const subPath = path?.length ? `/${path.join("/")}` : "";
  return proxyAuthenticatedApi(request, `/transcription${subPath}`);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const subPath = path?.length ? `/${path.join("/")}` : "";
  return proxyAuthenticatedApi(request, `/transcription${subPath}`);
}
