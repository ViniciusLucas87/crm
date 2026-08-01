import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

// GET /api/documents — list documents
export async function GET(request: NextRequest) {
  return proxyAuthenticatedApi(request, `/documents/${request.nextUrl.search}`);
}

// POST /api/documents — upload document
export async function POST(request: NextRequest) {
  return proxyAuthenticatedApi(request, `/documents/upload${request.nextUrl.search}`);
}
