import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

// Compatibility alias for older clients; the backend's supported endpoint is /mcp/message.
export async function POST(request: NextRequest) { return proxyAuthenticatedApi(request, "/mcp/message"); }
