"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Phone } from "lucide-react";
import type { Contact } from "@/lib/types";

type CallButtonProps = {
  companyId: number;
  callState: string;
  onCall: (id: number, phone: string, name: string) => void;
  /** Optional: pass contacts directly instead of fetching */
  contacts?: Contact[];
};

export function CallButton({ companyId, callState, onCall, contacts: externalContacts }: CallButtonProps) {
  const [contacts, setContacts] = useState<Contact[]>(externalContacts || []);
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    if (externalContacts) {
      setContacts(externalContacts);
      return;
    }
    fetch(`/api/contacts?company_id=${companyId}&page_size=20`)
      .then(r => r.ok ? r.json() : null)
      .then(d => d?.items && setContacts(d.items))
      .catch(() => {});
  }, [companyId, externalContacts]);

  const contactsWithPhones = contacts.filter(c => c.phone || c.mobile);
  const primaryContact = contactsWithPhones.find(c => c.isPrimary);

  if (contactsWithPhones.length === 0) {
    return (
      <div className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-500">
        <Phone className="h-4 w-4" />
        No contact with phone — <Link href={`/companies/${companyId}?tab=contacts`} className="text-cyan-400 hover:underline">add one</Link>
      </div>
    );
  }

  const isCallActive = callState !== "idle" && callState !== "ended" && callState !== "failed";

  // Single contact — direct call button
  if (contactsWithPhones.length === 1) {
    const c = contactsWithPhones[0];
    const display = `${c.firstName} ${c.lastName} (${c.phone || c.mobile})`;
    return (
      <button
        onClick={() => onCall(companyId, c.phone || c.mobile!, `${c.firstName} ${c.lastName}`)}
        disabled={isCallActive}
        className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-400/20 hover:border-emerald-400/50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Phone className="h-4 w-4" />
        {isCallActive ? "On a call…" : `Call ${display}`}
      </button>
    );
  }

  // Multiple contacts — dropdown picker
  const defaultContact = primaryContact || contactsWithPhones[0];
  return (
    <div className="relative">
      <button
        onClick={() => setShowPicker(!showPicker)}
        disabled={isCallActive}
        className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-400/20 hover:border-emerald-400/50 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Phone className="h-4 w-4" />
        {isCallActive ? "On a call…" : `Call ${defaultContact.firstName} ${defaultContact.lastName} ▾`}
      </button>
      {showPicker && (
        <div className="absolute top-full left-0 mt-1 z-50 rounded-xl border border-white/10 bg-slate-900 shadow-xl p-2 min-w-[240px]">
          {contactsWithPhones.map(c => (
            <button
              key={c.id}
              onClick={() => { onCall(companyId, c.phone || c.mobile!, `${c.firstName} ${c.lastName}`); setShowPicker(false); }}
              className="w-full text-left rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/10 transition"
            >
              <span className="text-white">{c.firstName} {c.lastName}</span>
              <span className="text-slate-500 ml-2">{c.phone || c.mobile}</span>
              {c.jobTitle && <span className="text-slate-600 ml-1">· {c.jobTitle}</span>}
              {c.isPrimary && <span className="ml-1 text-xs text-cyan-400">· Primary</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
