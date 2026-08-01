"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Users, Star } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { listContacts, createContact, updateContact, deleteContact } from "@/lib/api";
import type { Contact, ContactCreateInput, ContactUpdateInput } from "@/lib/types";

type Props = { companyId: number };

export function CompanyContactsTab({ companyId }: Props) {
  const { toast } = useToast();
  const nameRef = useRef<HTMLInputElement>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [form, setForm] = useState({ firstName: "", lastName: "", jobTitle: "", email: "", phone: "" });

  const fetchContacts = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const r = await listContacts(companyId, { pageSize: 50 });
      setContacts(r.items); setTotal(r.total);
    } catch (e) { setError(e instanceof Error ? e.message : "Failed"); }
    finally { setLoading(false); }
  }, [companyId]);

  useEffect(() => { void fetchContacts(); }, [fetchContacts]);

  const resetForm = () => { setForm({ firstName: "", lastName: "", jobTitle: "", email: "", phone: "" }); setEditingId(null); };

  const submitForm = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.firstName.trim() || !form.lastName.trim()) { setError("First and last name are required."); return; }
    setError(null);
    try {
      const input: ContactCreateInput = { companyId, firstName: form.firstName.trim(), lastName: form.lastName.trim(), jobTitle: form.jobTitle.trim() || undefined, email: form.email.trim() || undefined, phone: form.phone.trim() || undefined };
      if (editingId) { await updateContact(editingId, input as ContactUpdateInput); toast("Contact updated"); }
      else { await createContact(input); toast("Contact added"); }
      resetForm(); await fetchContacts(); nameRef.current?.focus();
    } catch (e) { setError(e instanceof Error ? e.message : "Failed"); toast(e instanceof Error ? e.message : "Error", "error"); }
  };

  const startEdit = (c: Contact) => { setEditingId(c.id); setForm({ firstName: c.firstName, lastName: c.lastName, jobTitle: c.jobTitle ?? "", email: c.email ?? "", phone: c.phone ?? "" }); nameRef.current?.focus(); };

  const archiveContact = async (id: number) => { setBusyId(id); try { await deleteContact(id); toast("Contact archived"); await fetchContacts(); } catch (e) { toast(e instanceof Error ? e.message : "Error", "error"); } finally { setBusyId(null); } };

  return (
    <div className="space-y-4">
      <Card>
        <form onSubmit={submitForm} className="flex flex-wrap items-end gap-3">
          <div className="w-full sm:w-40"><label htmlFor="ct-first" className="mb-1 block text-xs text-slate-500">First Name</label><Input id="ct-first" ref={nameRef} placeholder="John" value={form.firstName} onChange={e => setForm(p => ({ ...p, firstName: e.target.value }))} /></div>
          <div className="w-full sm:w-40"><label htmlFor="ct-last" className="mb-1 block text-xs text-slate-500">Last Name</label><Input id="ct-last" placeholder="Smith" value={form.lastName} onChange={e => setForm(p => ({ ...p, lastName: e.target.value }))} /></div>
          <div className="w-full sm:w-40"><label htmlFor="ct-title" className="mb-1 block text-xs text-slate-500">Title</label><Input id="ct-title" placeholder="CEO" value={form.jobTitle} onChange={e => setForm(p => ({ ...p, jobTitle: e.target.value }))} /></div>
          <div className="w-full sm:w-48"><label htmlFor="ct-email" className="mb-1 block text-xs text-slate-500">Email</label><Input id="ct-email" placeholder="john@company.com" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} /></div>
          <div className="w-full sm:w-36"><label htmlFor="ct-phone" className="mb-1 block text-xs text-slate-500">Phone</label><Input id="ct-phone" placeholder="555-0100" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} /></div>
          <div className="flex items-end gap-2">
            <Button type="submit" variant="primary">{editingId ? "Update" : "Add"}</Button>
            {editingId && <Button variant="secondary" onClick={resetForm}>Cancel</Button>}
          </div>
        </form>
      </Card>

      {error && <div role="alert" className="rounded-xl border border-red-400/20 bg-red-950/40 px-4 py-3 text-sm text-red-300">{error}</div>}

      {loading ? <TableSkeleton rows={3} /> : contacts.length === 0 ? (
        <EmptyState icon={Users} title="No contacts yet" description="Add your first contact for this company." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-900/40">
          <table className="w-full min-w-[600px]">
            <thead><tr className="border-b border-white/5 text-left">{["Name","Title","Email","Phone","Status","Actions"].map(h=><th key={h} className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">{h}</th>)}</tr></thead>
            <tbody>
              {contacts.map(c => (
                <tr key={c.id} className="border-t border-white/5 hover:bg-white/[0.02]">
                  <td className="px-4 py-3"><p className="font-medium text-slate-100">{c.firstName} {c.lastName}</p>{c.isDecisionMaker && <Star className="ml-1 inline h-3 w-3 text-amber-400" />}</td>
                  <td className="px-4 py-3 text-sm text-slate-400">{c.jobTitle ?? "-"}</td>
                  <td className="px-4 py-3 text-sm text-slate-400">{c.email ?? "-"}</td>
                  <td className="px-4 py-3 text-sm text-slate-400">{c.phone ?? "-"}</td>
                  <td className="px-4 py-3"><Badge variant={c.status === "active" ? "success" : "neutral"}>{c.status}</Badge></td>
                  <td className="px-4 py-3"><div className="flex gap-1.5"><Button variant="ghost" onClick={() => startEdit(c)}>Edit</Button><Button variant="danger" disabled={busyId === c.id} onClick={() => archiveContact(c.id)}>Archive</Button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {total > 0 && <p className="text-xs text-slate-500">{total} contact{total !== 1 ? "s" : ""}</p>}
    </div>
  );
}
