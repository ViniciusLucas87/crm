"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { CompaniesScreen } from "@/components/companies/companies-screen";
import { Shell } from "@/components/dashboard/shell";

export default function CompaniesPage() {
  const router = useRouter();
  const { isLoaded, userId } = useAuth();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (isLoaded) {
      if (!userId) {
        router.replace("/sign-in");
      } else {
        setReady(true);
      }
    }
  }, [isLoaded, userId, router]);

  if (!ready) return null;

  return (
    <Shell>
      <CompaniesScreen />
    </Shell>
  );
}
