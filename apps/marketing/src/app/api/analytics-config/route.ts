import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const validMeasurementId = (value: string | undefined) =>
  Boolean(value && /^G-[A-Z0-9]+$/.test(value));

export function GET() {
  const measurementId = process.env.GA_MEASUREMENT_ID?.trim();

  if (!validMeasurementId(measurementId)) {
    return new NextResponse(null, { status: 204 });
  }

  return NextResponse.json(
    { measurementId },
    { headers: { "Cache-Control": "no-store" } },
  );
}
