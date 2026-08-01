import { NextRequest } from "next/server";
import { proxyAuthenticatedApi } from "@/app/api/_utils";

export async function GET(request: NextRequest) { return proxyAuthenticatedApi(request, "/opportunities"); }
export async function POST(request: NextRequest) { return proxyAuthenticatedApi(request, "/opportunities"); }
