"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import type { Route } from "next";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Building2, Search, Sparkles } from "lucide-react";
import { ApiError, archiveCompany, createCompany, duplicateCompany, listCompanies, restoreCompany, updateCompany } from "@/lib/api";
import type { Company, CompanyCreateInput } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableRow, TableCell } from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

type FormState = { name: string; industry: string; website: string; email: string; owner: string };

const emptyForm: FormState = { name: "", industry: "", website: "", email: "", owner: "" };

const signInRoute = "/sign-in" as Route;

function formatApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.status === 401)
    return "Authentication is required before companies can be viewed or changed.";
  if (error instanceof ApiError && error.status === 403)
    return "Your account is signed in, but it does not have permission to perform this action.";
  if (error instanceof ApiError && error.status >= 500)
    return "The server is unavailable right now. Please try again shortly.";
  return error instanceof Error ? error.message : fallback;
}

export function CompaniesScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const aiTool = searchParams.get("ai");
  const { toast } = useToast();
  const nameInputRef = useRef<HTMLInputElement>(null);

  const AI_LABELS: Record<string, string> = {
    "company-analysis": "Company Analysis",
    proposals: "Proposal Builder",
    "meeting-prep": "Meeting Preparation",
    email: "Email Assistant",
    call: "Call Assistant",
  };

  const getCompanyHref = (companyId: number): Route =>
    aiTool ? `/ai/${aiTool}/${companyId}` as Route : `/companies/${companyId}` as Route;

  const [items, setItems] = useState<Company[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const fetchRows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listCompanies({
        page, pageSize,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        sortBy, sortDir, includeArchived,
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) { router.replace(signInRoute); return; }
      setError(formatApiError(err, "Failed to load companies"));
    } finally {
      setLoading(false);
    }
  }, [includeArchived, page, pageSize, router, search, sortBy, sortDir, statusFilter]);

  useEffect(() => { void fetchRows(); }, [fetchRows]);

  const resetForm = () => { setForm(emptyForm); setEditingId(null); };

  const submitForm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const payload: CompanyCreateInput = {
      name: form.name.trim(),
      industry: form.industry.trim() || undefined,
      website: form.website.trim() || undefined,
      email: form.email.trim() || undefined,
      owner: form.owner.trim() || undefined,
    };
    if (!payload.name) { setError("Company name is required."); nameInputRef.current?.focus(); return; }
    setError(null);
    try {
      if (editingId) { await updateCompany(editingId, payload); toast("Company updated", "success"); }
      else { await createCompany(payload); toast("Company created", "success"); }
      resetForm();
      await fetchRows();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) { router.replace(signInRoute); return; }
      const msg = formatApiError(err, "Failed to save company");
      setError(msg); toast(msg, "error");
    }
  };

  const startEdit = (company: Company) => {
    setEditingId(company.id);
    setForm({ name: company.name, industry: company.industry ?? "", website: company.website ?? "", email: company.email ?? "", owner: company.owner ?? "" });
    nameInputRef.current?.focus();
  };

  const runRowAction = async (companyId: number, action: () => Promise<unknown>, label: string) => {
    setBusyId(companyId); setError(null);
    try { await action(); toast(label, "success"); await fetchRows(); }
    catch (err) {
      if (err instanceof ApiError && err.status === 401) { router.replace(signInRoute); return; }
      const msg = formatApiError(err, "Action failed");
      setError(msg); toast(msg, "error");
    } finally { setBusyId(null); }
  };

  return (
    <div className="space-y-6">
      {/* Create / Edit Form */}
      <Card>
        <form onSubmit={submitForm} className="flex flex-wrap items-end gap-3">
          <div className="min-w-0 flex-1">
            <label htmlFor="co-name" className="mb-1.5 block text-xs font-medium text-slate-500">Company name</label>
            <Input id="co-name" ref={nameInputRef} placeholder="Acme Inc." value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div className="w-full sm:w-44">
            <label htmlFor="co-industry" className="mb-1.5 block text-xs font-medium text-slate-500">Industry</label>
            <Input id="co-industry" placeholder="Technology" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
          </div>
          <div className="w-full sm:w-44">
            <label htmlFor="co-website" className="mb-1.5 block text-xs font-medium text-slate-500">Website</label>
            <Input id="co-website" placeholder="https://" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} />
          </div>
          <div className="w-full sm:w-44">
            <label htmlFor="co-owner" className="mb-1.5 block text-xs font-medium text-slate-500">Owner email</label>
            <Input id="co-owner" placeholder="owner@company.com" value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} />
          </div>
          <div className="flex items-end gap-2">
            <Button type="submit" variant="primary">{editingId ? "Update" : "Create"}</Button>
            {editingId && <Button type="button" variant="secondary" onClick={resetForm}>Cancel</Button>}
          </div>
        </form>
      </Card>

      {/* AI Tool Banner */}
      {aiTool && (
        <Card className="border-cyan-400/10 bg-gradient-to-r from-cyan-950/40 to-violet-950/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-cyan-400/15 p-2 text-cyan-300"><Sparkles className="h-4 w-4" /></div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.1em] text-cyan-400">{AI_LABELS[aiTool] || aiTool}</p>
                <p className="text-sm text-slate-400">Select a company below to use this AI tool</p>
              </div>
            </div>
            <Link href="/companies" className="rounded-lg px-3 py-1.5 text-xs text-slate-500 transition hover:text-slate-300">
              <ArrowLeft className="mr-1 inline h-3 w-3" />Back to Companies
            </Link>
          </div>
        </Card>
      )}

      {/* Error banner */}
      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-xl border border-red-400/20 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          <span className="text-base leading-none">!</span>
          <p>{error}</p>
          <button type="button" onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200" aria-label="Dismiss error">&times;</button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1" style={{ minWidth: "200px" }}>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input hasLeftIcon placeholder="Search companies" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} aria-label="Search companies" />
        </div>
        <Select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} aria-label="Filter by status">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="lead">Lead</option>
          <option value="customer">Customer</option>
          <option value="archived">Archived</option>
        </Select>
        <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)} aria-label="Sort by">
          <option value="created_at">Created</option>
          <option value="updated_at">Updated</option>
          <option value="name">Name</option>
          <option value="revenue">Revenue</option>
          <option value="employees">Employees</option>
        </Select>
        <Button variant="secondary" onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))} aria-label={`Sort ${sortDir === "asc" ? "ascending" : "descending"}`}>
          Sort: {sortDir.toUpperCase()}
        </Button>
        <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 px-3 py-2.5 text-sm text-slate-400 transition hover:border-white/20 has-[:checked]:border-cyan-400/30 has-[:checked]:text-cyan-200">
          <input type="checkbox" className="h-3.5 w-3.5 rounded border-white/20 bg-white/10 text-cyan-400 focus:ring-cyan-400/30" checked={includeArchived} onChange={(e) => { setIncludeArchived(e.target.checked); setPage(1); }} />
          Include archived
        </label>
      </div>

      {/* Table */}
      <Table>
        <TableHeader columns={["Company", "Owner", "Industry", "Employees", "Revenue", "Status", "Last Activity", "Actions"]} />
        <tbody>
          {loading ? (
            <tr><td className="px-3 py-8" colSpan={8}><TableSkeleton rows={4} /></td></tr>
          ) : items.length === 0 ? (
            <tr><td className="px-3 py-12" colSpan={8}>
              <EmptyState
                icon={Building2}
                title="No companies yet"
                description={search ? "No companies match your search. Try adjusting your filters." : "Create your first company to begin building your sales pipeline."}
                action={search ? undefined : { label: "Create Company", onClick: () => nameInputRef.current?.focus() }}
              />
            </td></tr>
          ) : (
            items.map((company) => {
              const rowBusy = busyId === company.id;
              return (
                <TableRow key={company.id}>
                  <td className="px-4 py-3">
                    <Link
                      href={getCompanyHref(company.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-slate-100 transition hover:text-cyan-300 focus:outline-none focus-visible:underline"
                    >
                      {company.name}
                    </Link>
                  </td>
                  <TableCell>{company.owner ?? "-"}</TableCell>
                  <TableCell>{company.industry ?? "-"}</TableCell>
                  <TableCell>{company.employees ?? "-"}</TableCell>
                  <TableCell className="text-slate-300">{company.revenue ? `$${Number(company.revenue).toLocaleString()}` : "-"}</TableCell>
                  <td className="px-4 py-3"><Badge variant="success">{company.status}</Badge></td>
                  <td className="px-4 py-3 text-sm text-slate-500">{new Date(company.updatedAt).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      <Button variant="ghost" onClick={() => startEdit(company)} aria-label={`Edit ${company.name}`}>Edit</Button>
                      <Button variant="ghost" disabled={rowBusy} onClick={() => runRowAction(company.id, () => duplicateCompany(company.id), "Company duplicated")} aria-label={`Duplicate ${company.name}`}>Duplicate</Button>
                      <Button variant="danger" disabled={rowBusy} onClick={() => runRowAction(company.id, () => company.isArchived ? restoreCompany(company.id) : archiveCompany(company.id), company.isArchived ? "Company restored" : "Company archived")} aria-label={`${company.isArchived ? "Restore" : "Archive"} ${company.name}`}>
                        {company.isArchived ? "Restore" : "Archive"}
                      </Button>
                    </div>
                  </td>
                </TableRow>
              );
            })
          )}
        </tbody>
      </Table>

      {/* Pagination */}
      {!loading && items.length > 0 && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-slate-500">Showing page {page} of {totalPages} ({total} total)</p>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} aria-label="Previous page">Previous</Button>
            <Button variant="secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} aria-label="Next page">Next</Button>
          </div>
        </div>
      )}
    </div>
  );
}
