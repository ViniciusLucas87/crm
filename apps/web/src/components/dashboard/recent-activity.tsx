import { Building2, Archive, Copy, Pencil, type LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";

type ActivityItem = {
  id: string;
  icon: LucideIcon;
  action: string;
  target: string;
  timestamp: string;
};

type RecentActivityProps = {
  items: ActivityItem[];
};

export function RecentActivity({ items }: RecentActivityProps) {
  return (
    <Card>
      <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-400">Recent Activity</h3>
      {items.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">Activity from your team will appear here.</p>
      ) : (
        <ul className="mt-4 space-y-1">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition hover:bg-white/5"
            >
              <div className="inline-flex shrink-0 rounded-lg border border-white/10 bg-white/5 p-1.5 text-slate-400">
                <item.icon className="h-3.5 w-3.5" />
              </div>
              <span className="flex-1 text-slate-300">
                <span className="font-medium text-slate-200">{item.action}</span>{" "}
                <span className="text-slate-400">{item.target}</span>
              </span>
              <time className="shrink-0 text-xs text-slate-500" dateTime={item.timestamp}>
                {item.timestamp}
              </time>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function buildCompanyActivity(companyName: string, action: "created" | "archived" | "duplicated" | "updated"): ActivityItem {
  const map: Record<string, { icon: LucideIcon; action: string }> = {
    created: { icon: Building2, action: "Created company" },
    archived: { icon: Archive, action: "Archived company" },
    duplicated: { icon: Copy, action: "Duplicated company" },
    updated: { icon: Pencil, action: "Updated company" },
  };
  const { icon, action: actionLabel } = map[action];
  return {
    id: crypto.randomUUID(),
    icon,
    action: actionLabel,
    target: companyName,
    timestamp: new Date().toLocaleDateString(),
  };
}
