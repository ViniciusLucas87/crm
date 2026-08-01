/**
 * Pacific North Systems — Component Library
 *
 * Organized imports for every future module.
 *
 * Usage:
 *   import { Button, Input } from "@/components/forms";
 *   import { Badge, Table } from "@/components/data-display";
 *   import { Shell } from "@/components/layout";
 *   import { useToast } from "@/components/feedback";
 *
 * UI primitives also available directly:
 *   import { Card } from "@/components/ui/card";
 */

// Layout
export { Shell } from "@/components/layout";

// Forms
export { Button, Input, Select } from "@/components/forms";

// Data Display
export { Badge, Table, TableHeader, TableRow, TableCell, EmptyState, Skeleton, KpiSkeleton, TableSkeleton } from "@/components/data-display";

// Feedback
export { ToastProvider, useToast } from "@/components/feedback";

// Dashboard
export { DashboardScreen } from "@/components/dashboard/dashboard-screen";
export { KpiGrid } from "@/components/dashboard/kpi-grid";
export { RecentActivity, buildCompanyActivity } from "@/components/dashboard/recent-activity";
