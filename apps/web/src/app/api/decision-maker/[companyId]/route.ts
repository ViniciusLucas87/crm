import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type Ctx = { params: Promise<{ companyId: string }> };
export async function GET(request: NextRequest, ctx: Ctx) {
  const { companyId } = await ctx.params;
  return proxyAuthenticatedApi(request, `/decision-maker/${companyId}`);
}
