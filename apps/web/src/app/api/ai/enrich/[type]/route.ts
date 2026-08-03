import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type Ctx = { params: Promise<{ type: string }> };
export async function POST(request: NextRequest, ctx: Ctx) {
  const { type } = await ctx.params;
  return proxyAuthenticatedApi(request, `/enrich/${type}`);
}
