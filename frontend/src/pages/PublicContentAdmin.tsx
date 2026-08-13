import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowLeft, Check, Edit3, Plus, RefreshCw, Search, Trash2, X } from "lucide-react";
import { Link } from "wouter";
import { toast } from "sonner";
import {
  createPublicContent,
  deletePublicContent,
  getAdminPublicContent,
  getCurrentUser,
  updatePublicContent,
  type AdminPublicContentItem,
  type AuthUser,
  type PublicContentValue,
} from "@/lib/api";

type FormState = {
  contentKey: string;
  locale: string;
  contentType: "text" | "json" | "number" | "boolean";
  contentValue: string;
  isActive: boolean;
  sortOrder: string;
};

const emptyForm: FormState = {
  contentKey: "",
  locale: "en-KE",
  contentType: "text",
  contentValue: "",
  isActive: true,
  sortOrder: "0",
};

function isAdmin(user: AuthUser | null) {
  const role = String(user?.role ?? "").toUpperCase();
  if (role === "ADMIN") return true;
  const roles = Array.isArray(user?.roles) ? user.roles : [];
  return roles.some((item) => String(item?.name ?? item).toUpperCase() === "ADMIN");
}

function valueForEditor(item: AdminPublicContentItem) {
  if (item.content_type === "text") return typeof item.value === "string" ? item.value : "";
  return JSON.stringify(item.value, null, 2);
}

function parseValue(type: FormState["contentType"], raw: string): PublicContentValue {
  if (type === "text") return raw;
  if (type === "number") {
    const value = Number(raw);
    if (!Number.isFinite(value)) throw new Error("Value must be a valid number.");
    return value;
  }
  if (type === "boolean") {
    if (raw !== "true" && raw !== "false") throw new Error("Boolean value must be true or false.");
    return raw === "true";
  }
  try {
    return JSON.parse(raw) as PublicContentValue;
  } catch {
    throw new Error("JSON value is not valid JSON.");
  }
}

export default function PublicContentAdmin() {
  const [items, setItems] = useState<AdminPublicContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const [locale, setLocale] = useState("en-KE");
  const [activeOnly, setActiveOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<AdminPublicContentItem | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const current = await getCurrentUser();
      const allowed = isAdmin(current);
      setAuthorized(allowed);
      if (!allowed) return;
      setItems(await getAdminPublicContent({ locale, activeOnly }));
    } catch (error) {
      setAuthorized(false);
      toast.error(error instanceof Error ? error.message : "Unable to load public content.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [locale, activeOnly]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((item) => item.content_key.toLowerCase().includes(needle));
  }, [items, query]);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setModalOpen(true);
  }

  function openEdit(item: AdminPublicContentItem) {
    setEditing(item);
    setModalOpen(true);
    setForm({
      contentKey: item.content_key,
      locale: item.locale,
      contentType: item.content_type as FormState["contentType"],
      contentValue: valueForEditor(item),
      isActive: item.is_active,
      sortOrder: String(item.sort_order),
    });
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const value = parseValue(form.contentType, form.contentValue);
      const payload = {
        content_key: form.contentKey.trim(),
        locale: form.locale.trim(),
        content_type: form.contentType,
        content_value: value,
        is_active: form.isActive,
        sort_order: Number(form.sortOrder || 0),
      };
      if (!payload.content_key) throw new Error("Content key is required.");
      if (!payload.locale) throw new Error("Locale is required.");
      if (editing) await updatePublicContent(editing.id, payload);
      else await createPublicContent(payload);
      toast.success(editing ? "Content updated" : "Content created");
      setEditing(null);
      setForm(emptyForm);
      setModalOpen(false);
      await load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to save content.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(item: AdminPublicContentItem) {
    if (!window.confirm(`Delete ${item.content_key}?`)) return;
    try {
      await deletePublicContent(item.id);
      toast.success("Content deleted");
      await load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to delete content.");
    }
  }

  if (loading) return <PageShell><div className="animate-pulse rounded-2xl border border-border bg-card p-8"><div className="h-7 w-56 rounded bg-muted"/><div className="mt-5 h-24 rounded bg-muted"/></div></PageShell>;
  if (!authorized) return <PageShell><div className="rounded-2xl border border-destructive/20 bg-card p-8"><h1 className="font-display text-3xl font-bold">Access denied</h1><p className="mt-2 text-sm text-muted-foreground">An administrator account is required to manage public content.</p><Link href="/" className="mt-6 inline-flex rounded-full bg-primary px-5 py-3 text-sm font-bold text-primary-foreground">Return home</Link></div></PageShell>;

  return <PageShell>
    <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div><Link href="/" className="mb-4 inline-flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground"><ArrowLeft size={16}/> Back</Link><h1 className="font-display text-4xl font-bold tracking-tight">Public content</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Manage database-backed public copy without changing the frontend code.</p></div>
      <button onClick={openCreate} className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-bold text-primary-foreground"><Plus size={17}/> Add content</button>
    </div>

    <div className="mt-8 grid gap-3 rounded-2xl border border-border bg-card p-4 sm:grid-cols-[1fr_auto_auto_auto]">
      <label className="relative block"><Search size={17} className="absolute left-3 top-3.5 text-muted-foreground"/><input value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search content keys" className="w-full rounded-xl border border-input bg-background py-3 pl-10 pr-4 text-sm outline-none focus:border-primary"/></label>
      <input value={locale} onChange={(e)=>setLocale(e.target.value)} aria-label="Locale" className="rounded-xl border border-input bg-background px-4 py-3 text-sm font-semibold outline-none focus:border-primary"/>
      <label className="flex items-center gap-2 rounded-xl border border-input px-4 py-3 text-sm font-semibold"><input type="checkbox" checked={activeOnly} onChange={(e)=>setActiveOnly(e.target.checked)} className="accent-primary"/> Active only</label>
      <button onClick={()=>void load()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-input px-4 py-3 text-sm font-bold"><RefreshCw size={16}/> Refresh</button>
    </div>

    <div className="mt-5 overflow-hidden rounded-2xl border border-border bg-card">
      <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-border bg-muted/30 text-xs uppercase tracking-wider text-muted-foreground"><tr><th className="px-5 py-4">Content key</th><th className="px-5 py-4">Type</th><th className="px-5 py-4">Locale</th><th className="px-5 py-4">Status</th><th className="px-5 py-4">Order</th><th className="px-5 py-4 text-right">Actions</th></tr></thead><tbody className="divide-y divide-border">{filtered.map((item)=><tr key={item.id} className="hover:bg-muted/20"><td className="px-5 py-4"><div className="font-mono text-xs font-bold text-foreground">{item.content_key}</div><div className="mt-1 max-w-[360px] truncate text-xs text-muted-foreground">{typeof item.value === "string" ? item.value : JSON.stringify(item.value)}</div></td><td className="px-5 py-4 font-semibold">{item.content_type}</td><td className="px-5 py-4 font-semibold">{item.locale}</td><td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${item.is_active ? "bg-success/10 text-success" : "bg-muted text-muted-foreground"}`}>{item.is_active ? "Active" : "Inactive"}</span></td><td className="px-5 py-4">{item.sort_order}</td><td className="px-5 py-4"><div className="flex justify-end gap-2"><button onClick={()=>openEdit(item)} aria-label={`Edit ${item.content_key}`} className="rounded-lg border border-border p-2 hover:bg-muted"><Edit3 size={15}/></button><button onClick={()=>void remove(item)} aria-label={`Delete ${item.content_key}`} className="rounded-lg border border-border p-2 text-destructive hover:bg-destructive/10"><Trash2 size={15}/></button></div></td></tr>)}{filtered.length===0 && <tr><td colSpan={6} className="px-5 py-16 text-center text-sm text-muted-foreground">No public content records match your filters.</td></tr>}</tbody></table></div>
    </div>

    {modalOpen && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-5"><div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-t-3xl bg-card p-6 shadow-2xl sm:rounded-3xl"><div className="flex items-start justify-between"><div><h2 className="font-display text-2xl font-bold">{editing ? "Edit content" : "Add content"}</h2><p className="mt-1 text-sm text-muted-foreground">Values are stored in the database and served through the public API.</p></div><button onClick={()=>{setEditing(null);setForm(emptyForm);setModalOpen(false)}} className="rounded-lg p-2 hover:bg-muted"><X size={18}/></button></div><form onSubmit={save} className="mt-6 grid gap-4"><label className="grid gap-1.5 text-sm font-bold">Content key<input value={form.contentKey} onChange={(e)=>setForm({...form,contentKey:e.target.value})} disabled={Boolean(editing)} placeholder="home.hero.title" className="rounded-xl border border-input bg-background px-4 py-3 font-mono text-sm font-normal outline-none focus:border-primary"/></label><div className="grid gap-4 sm:grid-cols-3"><label className="grid gap-1.5 text-sm font-bold">Locale<input value={form.locale} onChange={(e)=>setForm({...form,locale:e.target.value})} className="rounded-xl border border-input bg-background px-4 py-3 font-normal outline-none focus:border-primary"/></label><label className="grid gap-1.5 text-sm font-bold">Type<select value={form.contentType} onChange={(e)=>setForm({...form,contentType:e.target.value as FormState["contentType"]})} className="rounded-xl border border-input bg-background px-4 py-3 font-normal outline-none focus:border-primary"><option value="text">Text</option><option value="json">JSON</option><option value="number">Number</option><option value="boolean">Boolean</option></select></label><label className="grid gap-1.5 text-sm font-bold">Sort order<input type="number" value={form.sortOrder} onChange={(e)=>setForm({...form,sortOrder:e.target.value})} className="rounded-xl border border-input bg-background px-4 py-3 font-normal outline-none focus:border-primary"/></label></div><label className="grid gap-1.5 text-sm font-bold">Value<textarea value={form.contentValue} onChange={(e)=>setForm({...form,contentValue:e.target.value})} rows={form.contentType === "text" ? 6 : 10} placeholder={form.contentType === "json" ? '{\n  "items": []\n}' : "Enter the database-backed value"} className="resize-y rounded-xl border border-input bg-background px-4 py-3 font-normal outline-none focus:border-primary"/></label><label className="flex items-center gap-2 text-sm font-semibold"><input type="checkbox" checked={form.isActive} onChange={(e)=>setForm({...form,isActive:e.target.checked})} className="accent-primary"/> Active on the public site</label><div className="flex justify-end gap-2 border-t border-border pt-5"><button type="button" onClick={()=>{setEditing(null);setForm(emptyForm);setModalOpen(false)}} className="rounded-xl border border-border px-5 py-3 text-sm font-bold">Cancel</button><button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground disabled:opacity-60">{saving?<RefreshCw size={16} className="animate-spin"/>:<Check size={16}/>} Save</button></div></form></div></div>}
  </PageShell>;
}

function PageShell({ children }: { children: React.ReactNode }) {
  return <main className="min-h-screen bg-background px-5 py-8 text-foreground lg:px-8"><div className="mx-auto max-w-7xl">{children}</div></main>;
}
