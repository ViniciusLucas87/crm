import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type RouteContext = {
  params: Promise<{ companyId: string }>;
};

export async function POST(request: NextRequest, context: RouteContext) {
  const { companyId } = await context.params;
  return proxyAuthenticatedApi(request, `/companies/${companyId}/restore`);
}