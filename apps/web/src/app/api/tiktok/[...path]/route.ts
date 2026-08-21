import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type RouteContext = { params: Promise<{ path: string[] }> };

function backendPath(path: string[], request: NextRequest) {
  return `/tiktok/${path.join("/")}${request.nextUrl.search}`;
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyAuthenticatedApi(request, backendPath((await context.params).path, request));
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyAuthenticatedApi(request, backendPath((await context.params).path, request));
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxyAuthenticatedApi(request, backendPath((await context.params).path, request));
}
