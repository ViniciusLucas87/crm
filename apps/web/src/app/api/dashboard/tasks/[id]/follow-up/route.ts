import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyAuthenticatedApi(request, `/tasks/${id}/follow-up`);
}
