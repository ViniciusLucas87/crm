"use client";

import Link from "next/link";
import type { Route } from "next";
import { ChevronRight } from "lucide-react";

export type Crumb = { label: string; href?: string };

type Props = { items: Crumb[]; className?: string };

export function Breadcrumbs({ items, className = "" }: Props) {
  return (
    <nav className={`flex items-center gap-1.5 text-xs text-slate-500 ${className}`} aria-label="Breadcrumb">
      <Link href="/" className="transition hover:text-slate-300">Home</Link>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          <ChevronRight className="h-3 w-3" />
          {item.href ? (
            <Link href={item.href as Route} className="transition hover:text-slate-300">
              {item.label}
            </Link>
          ) : (
            <span className="text-slate-300">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
