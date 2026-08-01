import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

export async function GET(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendPath = `/leads/${path.join("/")}${request.nextUrl.search}`;
  return proxyAuthenticatedApi(request, backendPath);
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendPath = `/leads/${path.join("/")}`;
  return proxyAuthenticatedApi(request, backendPath);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendPath = `/leads/${path.join("/")}`;
  return proxyAuthenticatedApi(request, backendPath);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendPath = `/leads/${path.join("/")}`;
  return proxyAuthenticatedApi(request, backendPath);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendPath = `/leads/${path.join("/")}`;
  return proxyAuthenticatedApi(request, backendPath);
}
