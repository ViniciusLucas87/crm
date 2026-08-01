"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

type TableProps = {
  children: ReactNode;
  className?: string;
};

export function Table({ children, className }: TableProps) {
  return (
    <div className={cn("overflow-x-auto rounded-2xl border border-white/10 bg-slate-900/40", className)}>
      <table className="w-full min-w-[800px]">{children}</table>
    </div>
  );
}

type TableHeaderProps = {
  columns: string[];
};

export function TableHeader({ columns }: TableHeaderProps) {
  return (
    <thead>
      <tr className="border-b border-white/5 text-left">
        {columns.map((col) => (
          <th key={col} className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
            {col}
          </th>
        ))}
      </tr>
    </thead>
  );
}

type TableRowProps = {
  children: ReactNode;
  className?: string;
};

export function TableRow({ children, className }: TableRowProps) {
  return (
    <tr className={cn("border-t border-white/5 transition-colors hover:bg-white/[0.02]", className)}>
      {children}
    </tr>
  );
}

type TableCellProps = {
  children: ReactNode;
  className?: string;
  colSpan?: number;
};

export function TableCell({ children, className, colSpan }: TableCellProps) {
  return (
    <td className={cn("px-4 py-3 text-sm text-slate-400", className)} colSpan={colSpan}>
      {children}
    </td>
  );
}
