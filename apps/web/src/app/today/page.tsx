"use client";

import dynamic from "next/dynamic";
import { Shell } from "@/components/dashboard/shell";

const TodayScreen = dynamic(
  () => import("@/components/dashboard/today-screen"),
  { ssr: false, loading: () => <TodayLoading /> }
);

function TodayLoading() {
  return (
    <div style={{ padding: "48px 32px", textAlign: "center", color: "#8B9DC3" }}>
      <p style={{ fontSize: 16 }}>Loading your Today workspace</p>
    </div>
  );
}

export default function TodayPage() {
  return (
    <Shell>
      <TodayScreen />
    </Shell>
  );
}
