"use client";

import { useClerk, useUser } from "@clerk/nextjs";
import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { Building2, CircleUserRound, LayoutDashboard, LogOut, Menu, Sparkles, X, Users, Target, ClipboardList, FolderKanban, FileText, FileCheck, BarChart3, Settings, Sun, Search, CalendarCheck2, Mail, Lightbulb, BookOpen, Phone, PhoneCall, Radar, FlaskConical, Signal, Bookmark, Send, Download, TrendingUp, Brain, Shield, Activity, PackageCheck, MessageCircle } from "lucide-react";
import { DashboardErrorBoundary } from "@/components/dashboard/error-boundary";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import { GlobalSearch } from "@/components/dashboard/global-search";
import { useNavigationMemory } from "@/lib/use-navigation-memory";

type ShellProps = {
  children: ReactNode;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

type NavItem = {
  label: string;
  icon: typeof LayoutDashboard;
  href: Route;
  active?: boolean;
};

const navigation: NavGroup[] = [
  {
    label: "Command Center",
    items: [
      { label: "Dashboard", icon: LayoutDashboard, href: "/" as Route, active: true },
      { label: "Today", icon: CalendarCheck2, href: "/today" as Route, active: true },
      { label: "Call Center Phone", icon: PhoneCall, href: "/call-center" as Route, active: true },
      { label: "Never Miss", icon: PackageCheck, href: "/products" as Route, active: true },
    ],
  },
  {
    label: "Sales",
    items: [
      { label: "Companies", icon: Building2, href: "/companies" as Route, active: true },
      { label: "Contacts", icon: Users, href: "#" as Route },
      { label: "Opportunities", icon: Target, href: "#" as Route },
      { label: "Activities", icon: Phone, href: "#" as Route },
      { label: "Tasks", icon: ClipboardList, href: "#" as Route },
    ],
  },
  {
    label: "Lead Intelligence",
    items: [
      { label: "Overview", icon: Radar, href: "/leads" as Route, active: true },
      { label: "Discover Companies", icon: Search, href: "/leads/discover" as Route, active: true },
      { label: "Reddit Opportunities", icon: MessageCircle, href: "/leads/reddit" as Route, active: true },
      { label: "Lead Workspace", icon: Building2, href: "/leads/workspace" as Route, active: true },
      { label: "Research Queue", icon: FlaskConical, href: "/leads/research-queue" as Route, active: true },
      { label: "Decision Makers", icon: Users, href: "/leads/decision-makers" as Route, active: true },
      { label: "Buying Signals", icon: Signal, href: "/leads/buying-signals" as Route, active: true },
      { label: "Saved Searches", icon: Bookmark, href: "/leads/saved-searches" as Route, active: true },
      { label: "Outreach Queue", icon: Send, href: "/leads/outreach-queue" as Route, active: true },
      { label: "Import Review", icon: Download, href: "/leads/import-review" as Route, active: true },
      { label: "Analytics", icon: TrendingUp, href: "/leads/analytics" as Route, active: true },
    ],
  },
  {
    label: "Delivery",
    items: [
      { label: "Projects", icon: FolderKanban, href: "#" as Route },
      { label: "Documents", icon: FileText, href: "#" as Route },
    ],
  },
  {
    label: "AI",
    items: [
      { label: "AI Explorer", icon: Brain, href: "/ai/explorer" as Route, active: true },
      { label: "Daily Brief", icon: Sun, href: "/ai/daily-brief" as Route, active: true },
      { label: "Company Analysis", icon: Lightbulb, href: "/companies?ai=company-analysis" as Route, active: true },
      { label: "Proposal Builder", icon: FileCheck, href: "/companies?ai=proposals" as Route, active: true },
      { label: "Meeting Preparation", icon: CalendarCheck2, href: "/companies?ai=meeting-prep" as Route, active: true },
      { label: "Email Assistant", icon: Mail, href: "/companies?ai=email" as Route, active: true },
      { label: "Call Assistant", icon: Phone, href: "/companies?ai=call" as Route, active: true },
      { label: "Opportunity Explorer", icon: Search, href: "/ai/explorer" as Route, active: true },
      { label: "Knowledge Base", icon: BookOpen, href: "/ai/knowledge-base" as Route, active: true },
    ],
  },
  {
    label: "Insights",
    items: [
      { label: "Reports", icon: BarChart3, href: "#" as Route },
      { label: "Settings", icon: Settings, href: "#" as Route },
    ],
  },
  {
    label: "Operations",
    items: [
      { label: "Audit Log", icon: Shield, href: "/audit" as Route, active: true },
      { label: "System Status", icon: Activity, href: "/operations" as Route, active: true },
    ],
  },
];

export function Shell({ children }: ShellProps) {
  const pathname = usePathname();
  const { signOut } = useClerk();
  const { user } = useUser();
  const { memory } = useNavigationMemory();
  const email = user?.primaryEmailAddress?.emailAddress ?? user?.emailAddresses?.[0]?.emailAddress ?? "Authenticated user";
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = window.localStorage.getItem("pns-theme");
    if (saved === "light" || saved === "dark") setTheme(saved);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("pns-theme", theme);
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  // Map string tool names to AI routes
  const AI_TOOL_ROUTES: Record<string, string> = {
    "Company Analysis": "company-analysis",
    "Proposal Builder": "proposals",
    "Meeting Preparation": "meeting",
    "Email Assistant": "email",
    "Call Assistant": "call",
  };

  const resolveHref = (label: string, defaultHref: string): Route => {
    if (AI_TOOL_ROUTES[label] && memory.lastCompanyId) {
      return `/ai/${AI_TOOL_ROUTES[label]}/${memory.lastCompanyId}` as Route;
    }
    return defaultHref as Route;
  };

  const sidebarContent = (
    <>
      <div className="mb-8 flex items-center gap-3">
        <div className="rounded-xl bg-cyan-300/15 p-2 text-cyan-200">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm text-cyan-200">Pacific North Systems</p>
          <h1 className="text-lg font-semibold tracking-tight">Sales OS</h1>
        </div>
      </div>
      <nav className="space-y-6" aria-label="Main navigation">
        {navigation.map((group) => (
          <div key={group.label}>
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-600">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map(({ label, icon: Icon, href, active }) => {
                const isActive = active && pathname === href;
                const isFuture = !active;
                const resolvedHref = resolveHref(label, href);
                const isPlaceholder = href === "#";

                // Dead links render as disabled buttons, not Link components
                if (isPlaceholder) {
                  return (
                    <button
                      key={label}
                      disabled
                      className={cn(
                        "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium text-slate-700",
                      )}
                      aria-disabled="true"
                      tabIndex={-1}
                    >
                      <Icon className="h-4 w-4" />
                      {label}
                    </button>
                  );
                }

                return (
                  <Link
                    key={label}
                    href={resolvedHref}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/50",
                      isActive && "bg-white/10 text-white shadow-[0_0_0_1px_rgba(255,255,255,0.06)]",
                      !isActive && !isFuture && "text-slate-400 hover:bg-white/5 hover:text-white",
                    )}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </>
  );

  return (
    <div className={cn("pns-shell min-h-screen", theme === "dark" ? "bg-[radial-gradient(circle_at_top,_#12343b,_#06131a_45%,_#02070a)] text-slate-100" : "bg-slate-100 text-slate-900")}>
      <div className="mx-auto flex w-full max-w-7xl flex-col lg:flex-row">
        {/* Desktop sidebar */}
        <aside className="hidden border-r border-white/10 p-4 lg:flex lg:min-h-screen lg:w-64 lg:flex-col">
          {sidebarContent}
        </aside>

        {/* Mobile header */}
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 lg:hidden">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-cyan-300/15 p-1.5 text-cyan-200">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="text-sm font-semibold">Sales OS</span>
          </div>
          <Button variant="secondary" onClick={() => setMobileOpen((prev) => !prev)} aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={mobileOpen}>
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>

        {/* Mobile drawer */}
        {mobileOpen && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} aria-hidden="true" />
            <aside className="fixed inset-y-0 left-0 w-64 border-r border-white/10 bg-slate-950/95 p-4 backdrop-blur-xl">
              {sidebarContent}
            </aside>
          </div>
        )}

        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-300/70">Founder Outbound Command</p>
              <h2 className="text-xl font-semibold tracking-tight text-white md:text-2xl">Daily Intelligence Dashboard</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <label className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <Sun className="h-4 w-4" aria-hidden="true" />
                <span className="sr-only">Colour theme</span>
                <select
                  aria-label="Colour theme"
                  value={theme}
                  onChange={(event) => setTheme(event.target.value as "dark" | "light")}
                  className="bg-transparent text-sm font-medium outline-none"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                </select>
              </label>
              <GlobalSearch />
              <div className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:border-white/15">
                <CircleUserRound className="h-4 w-4 text-slate-400" />
                <span className="max-w-[160px] truncate">{email}</span>
              </div>
              <Button variant="danger" onClick={() => void signOut({ redirectUrl: "/sign-in" })} aria-label="Sign out of your account">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </Button>
            </div>
          </header>
          <DashboardErrorBoundary>
            {children}
          </DashboardErrorBoundary>
        </main>
      </div>
    </div>
  );
}
