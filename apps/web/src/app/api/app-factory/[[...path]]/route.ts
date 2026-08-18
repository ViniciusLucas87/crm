import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type RouteContext = { params: Promise<{ path?: string[] }> };

function backendPath(path?: string[]) {
  return `/app-factory${path?.length ? `/${path.join("/")}` : ""}`;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyAuthenticatedApi(request, `${backendPath(path)}${request.nextUrl.search}`);
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxyAuthenticatedApi(request, backendPath(path));
}
