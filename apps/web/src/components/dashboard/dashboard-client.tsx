"use client";

import { Shell } from "@/components/dashboard/shell";
import { DashboardScreen } from "@/components/dashboard/dashboard-screen";

export function DashboardClient() {
  return (
    <Shell>
      <DashboardScreen />
    </Shell>
  );
}
