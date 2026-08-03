import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type Ctx = { params: Promise<{ agent: string }> };
export async function GET(request: NextRequest, ctx: Ctx) {
  const { agent } = await ctx.params;
  return proxyAuthenticatedApi(request, `/agents/${agent}`);
}
