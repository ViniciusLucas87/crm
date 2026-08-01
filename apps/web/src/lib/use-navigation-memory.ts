"use client";

import { useCallback, useState } from "react";

const STORAGE_KEY = "pns_nav_memory";

type NavMemory = {
  lastCompanyId: number | null;
  lastCompanyName: string;
  lastFilters: Record<string, string>;
  lastSearch: string;
  lastTab: string;
};

function load(): NavMemory {
  if (typeof window === "undefined") return { lastCompanyId: null, lastCompanyName: "", lastFilters: {}, lastSearch: "", lastTab: "" };
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") as NavMemory || { lastCompanyId: null, lastCompanyName: "", lastFilters: {}, lastSearch: "", lastTab: "" };
  } catch { return { lastCompanyId: null, lastCompanyName: "", lastFilters: {}, lastSearch: "", lastTab: "" }; }
}

function save(m: Partial<NavMemory>) {
  if (typeof window === "undefined") return;
  const current = load();
  const merged = { ...current, ...m };
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(merged)); } catch { /* quota exceeded — ignore */ }
}

export function useNavigationMemory() {
  const [memory, setMemory] = useState<NavMemory>(load);

  const rememberCompany = useCallback((id: number, name: string) => {
    save({ lastCompanyId: id, lastCompanyName: name });
    setMemory(prev => ({ ...prev, lastCompanyId: id, lastCompanyName: name }));
  }, []);

  const rememberFilters = useCallback((filters: Record<string, string>) => {
    save({ lastFilters: filters });
    setMemory(prev => ({ ...prev, lastFilters: filters }));
  }, []);

  const rememberTab = useCallback((tab: string) => {
    save({ lastTab: tab });
    setMemory(prev => ({ ...prev, lastTab: tab }));
  }, []);

  return { memory, rememberCompany, rememberFilters, rememberTab };
}
