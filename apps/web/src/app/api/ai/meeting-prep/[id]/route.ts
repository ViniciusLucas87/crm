import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

type Ctx = { params: Promise<{ id: string }> };
export async function GET(request: NextRequest, ctx: Ctx) {
  const { id } = await ctx.params;
  return proxyAuthenticatedApi(request, `/ai/meeting-prep/${id}`);
}
