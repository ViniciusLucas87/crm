"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { Bookmark, Search, Trash2, Plus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";

type Saved = { id: number; name: string; filters: Record<string, string>; created_at: string };

export default function SavedSearchesPage() {
  const [searches, setSearches] = useState<Saved[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");

  const fetchSearches = () => {
    setLoading(true);
    fetch("/api/leads/saved/list")
      .then(r => r.json())
      .then(d => setSearches(d.items || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchSearches(); }, []);

  const saveSearch = async () => {
    if (!newName.trim()) return;
    await fetch("/api/leads/saved", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, filters_json: JSON.stringify({ name: newName }) }),
    });
    setNewName("");
    fetchSearches();
  };

  const deleteSearch = async (id: number) => {
    await fetch(`/api/leads/saved/${id}`, { method: "DELETE" });
    fetchSearches();
  };

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Lead Intelligence", href: "/leads" }, { label: "Saved Searches" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Saved Searches</h2>
          <p className="text-sm text-slate-400">Quick-access discovery filters for one-click research.</p>
        </div>
        <Link href="/leads/discover" className="text-xs text-slate-400 hover:text-cyan-300">← Discover</Link>
      </div>

      {/* New saved search */}
      <Card>
        <div className="flex gap-2">
          <input
            type="text" placeholder="Search name (e.g., Construction Vancouver)..."
            value={newName} onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === "Enter" && saveSearch()}
            className="flex-1 rounded-lg border border-white/10 bg-slate-800/50 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none"
          />
          <Button variant="primary" onClick={saveSearch}><Plus className="mr-1 h-3.5 w-3.5" />Save</Button>
        </div>
      </Card>

      {loading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 rounded-xl" />)}</div>
      ) : searches.length === 0 ? (
        <Card className="border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5">
          <div className="py-12 text-center">
            <Bookmark className="mx-auto h-10 w-10 text-cyan-400" />
            <h3 className="mt-3 text-lg font-semibold text-white">No Saved Searches</h3>
            <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
              Save your favorite discovery filters for one-click prospect research.
              Future releases will support scheduled execution.
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-2">
          {searches.map(s => (
            <Card key={s.id} className="flex items-center justify-between">
              <Link href={`/leads/discover?saved=${s.id}` as Route} className="flex items-center gap-3 flex-1">
                <Bookmark className="h-5 w-5 text-cyan-400" />
                <div>
                  <p className="font-medium text-white">{s.name}</p>
                  <p className="text-xs text-slate-500">
                    {Object.entries(s.filters).map(([k, v]) => `${k}: ${v}`).join(", ") || "No filters"}
                  </p>
                </div>
              </Link>
              <div className="flex items-center gap-2">
                <Link href={`/leads/discover?saved=${s.id}` as Route}>
                  <Search className="h-4 w-4 text-slate-400 hover:text-cyan-400" />
                </Link>
                <button onClick={() => deleteSearch(s.id)}><Trash2 className="h-4 w-4 text-slate-600 hover:text-red-400" /></button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
