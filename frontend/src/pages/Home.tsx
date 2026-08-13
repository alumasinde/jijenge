import { useEffect, useMemo, useState } from "react";
import { Link } from "wouter";
import {
  ArrowUpRight, Bell, Check, ChevronRight, Compass, LogOut,
  Menu, Search, Sparkles, UserRound, X,
} from "lucide-react";
import { toast } from "sonner";
import {
  clearTokens, getAccessToken, getCategories, getCurrentUser, getServices,
  type AuthUser, type Service, type ServiceCategory,
} from "@/lib/api";
import { useBranding } from "@/contexts/BrandingContext";
import { usePublicContent } from "@/contexts/PublicContentContext";

function Logomark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" role="img" aria-hidden="true">
      <circle cx="20" cy="20" r="20" className="fill-primary" />
      <circle cx="20" cy="20" r="8" className="fill-accent" />
      <circle cx="20" cy="7" r="2.4" className="fill-accent" />
      <circle cx="20" cy="33" r="2.4" className="fill-accent" />
      <circle cx="7" cy="20" r="2.4" className="fill-accent" />
      <circle cx="33" cy="20" r="2.4" className="fill-accent" />
    </svg>
  );
}

function Logo({ compact = false }: { compact?: boolean }) {
  const { branding } = useBranding();
  return (
    <div className="flex items-center gap-2.5">
      {branding.logo_url ? (
        <img src={branding.logo_url} alt={branding.app_name} className="h-9 w-auto object-contain" />
      ) : <Logomark />}
      {!compact && <span className="font-display text-2xl font-bold tracking-[-.04em]">{branding.short_name}</span>}
    </div>
  );
}

function ServiceCard({ service, onOpen }: { service: Service; onOpen: (service: Service) => void }) {
  return (
    <button onClick={() => onOpen(service)}
      className="group flex h-full flex-col justify-between rounded-xl border border-border bg-card p-5 text-left shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md active:scale-[.98]">
      <div>
        <div className="mb-6 flex items-start justify-between">
          <span className="grid size-11 place-items-center rounded-full bg-accent/10 text-lg font-semibold text-accent">
            {service.category_name.charAt(0)}
          </span>
          <ChevronRight size={16} className="mt-2 text-muted-foreground transition group-hover:translate-x-1" />
        </div>
        <p className="mb-2 text-[11px] font-bold uppercase tracking-[.16em] text-accent">{service.category_name}</p>
        <h3 className="font-display text-[1.5rem] font-bold leading-[1.02] tracking-[-.03em]">{service.name}</h3>
        <p className="mt-3 line-clamp-2 text-sm leading-6 text-muted-foreground">
          {service.description || ""}
        </p>
      </div>
    </button>
  );
}

export default function Home() {
  const { branding } = useBranding();
  const { text, list, loading: contentLoading, error: contentError } = usePublicContent();
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("");
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [selected, setSelected] = useState<Service | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    void getCategories().then(setCategories).catch(() => toast.error(text("system.errors.categories_load")));
    void getServices().then(setServices).catch(() => toast.error(text("system.errors.services_load")));
    if (getAccessToken()) void getCurrentUser().then(setUser).catch(() => clearTokens());
  }, [text]);

  useEffect(() => {
    if (!activeCategory && text("home.filters.all_services")) {
      setActiveCategory(text("home.filters.all_services"));
    }
  }, [activeCategory, text]);

  const filtered = useMemo(() => services.filter((service) => {
    const matchesCategory = !activeCategory || activeCategory === text("home.filters.all_services")
      || service.category_id === categories.find((category) => category.name === activeCategory)?.id;
    const haystack = `${service.name} ${service.description ?? ""} ${service.category_name}`.toLowerCase();
    const matchesQuery = !query.trim() || haystack.includes(query.trim().toLowerCase());
    return matchesCategory && matchesQuery;
  }), [services, categories, activeCategory, query, text]);

  const comingSoon = (label: string) =>
    toast(label, { description: text("system.messages.coming_soon") });

  if (contentLoading) {
    return <div className="grid min-h-screen place-items-center bg-background text-foreground"><div className="size-8 animate-spin rounded-full border-2 border-border border-t-primary" /></div>;
  }

  if (contentError) {
    return <div className="grid min-h-screen place-items-center bg-background px-5 text-center text-foreground"><div><p className="font-display text-2xl font-bold">{text("system.errors.content_unavailable")}</p><button onClick={() => window.location.reload()} className="mt-4 rounded-full bg-primary px-5 py-3 text-sm font-bold text-primary-foreground">{text("system.actions.retry")}</button></div></div>;
  }

  const trustItems = list("home.trust.items");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1320px] items-center justify-between px-5 py-4 lg:px-10">
          <a href="#top" aria-label={text("navigation.home_aria")}><Logo /></a>
          <nav className="hidden items-center gap-8 text-xs font-bold uppercase tracking-[.16em] text-muted-foreground md:flex">
            <a className="text-foreground" href="#discover">{text("navigation.find_service")}</a>
            <Link href="/find-providers" className="transition hover:text-foreground">{text("navigation.providers_near_me")}</Link>
            <button onClick={() => comingSoon(text("navigation.post_job"))} className="transition hover:text-foreground">{text("navigation.post_job")}</button>
          </nav>
          <div className="flex items-center gap-2">
            <button aria-label={text("navigation.notifications")} onClick={() => comingSoon(text("navigation.notifications"))} className="hidden size-10 place-items-center rounded-full border border-border md:grid"><Bell size={16} /></button>
            {user ? (
              <button onClick={() => { clearTokens(); setUser(null); toast(text("auth.messages.signed_out")); }} className="hidden items-center gap-2 rounded-full bg-primary px-4 py-2.5 text-xs font-bold uppercase tracking-[.14em] text-primary-foreground sm:flex">
                <LogOut size={14} /> {text("navigation.sign_out")}
              </button>
            ) : (
              <Link href="/login" className="hidden rounded-full bg-primary px-4 py-2.5 text-xs font-bold uppercase tracking-[.14em] text-primary-foreground sm:block">{text("navigation.sign_in")}</Link>
            )}
            <button aria-label={text("navigation.menu")} onClick={() => setMenuOpen(!menuOpen)} className="grid size-10 place-items-center rounded-full border border-border md:hidden">{menuOpen ? <X size={18} /> : <Menu size={18} />}</button>
          </div>
        </div>
        {menuOpen && <div className="border-t border-border bg-background px-5 py-4 md:hidden"><div className="grid gap-4 text-sm font-bold">
          <a href="#discover" onClick={() => setMenuOpen(false)}>{text("navigation.find_service")}</a>
          <Link href="/find-providers" onClick={() => setMenuOpen(false)}>{text("navigation.providers_near_me")}</Link>
          <button className="text-left" onClick={() => comingSoon(text("navigation.post_job"))}>{text("navigation.post_job")}</button>
          {user ? <button className="text-left" onClick={() => { clearTokens(); setUser(null); setMenuOpen(false); }}>{text("navigation.sign_out")}</button> : <Link href="/login" onClick={() => setMenuOpen(false)}>{text("navigation.sign_in")}</Link>}
        </div></div>}
      </header>

      <main id="top">
        <section className="relative overflow-hidden border-b border-border">
          <div className="mx-auto grid max-w-[1320px] items-stretch lg:grid-cols-[.92fr_1.08fr]">
            <div className="relative z-10 flex flex-col justify-center px-5 py-16 sm:py-24 lg:px-10 lg:py-28">
              <div className="mb-8 flex items-center gap-3 text-xs font-bold uppercase tracking-[.18em] text-accent"><span className="inline-block size-2 rounded-full bg-accent" />{text("home.hero.eyebrow")}</div>
              <h1 className="max-w-xl font-display text-[clamp(3.2rem,7vw,6.4rem)] font-bold leading-[.9] tracking-[-.06em]">{text("home.hero.title")}</h1>
              <p className="mt-8 max-w-md text-base leading-7 text-muted-foreground sm:text-lg">{text("home.hero.description")}</p>
              <div className="mt-10 flex flex-wrap gap-3">
                <a href="#discover" className="inline-flex items-center gap-3 rounded-full bg-primary px-5 py-3.5 text-sm font-bold text-primary-foreground">{text("home.hero.primary_action")} <ArrowUpRight size={17} /></a>
                <Link href="/find-providers" className="inline-flex items-center gap-2 rounded-full border border-border px-5 py-3.5 text-sm font-bold transition hover:bg-muted">{text("home.hero.secondary_action")}</Link>
              </div>
            </div>
            <div className="relative min-h-[280px] overflow-hidden lg:min-h-[560px]">
              <div className="absolute inset-0" style={{ backgroundImage: "radial-gradient(circle at 20% 20%, rgb(var(--brand-accent-rgb) / .35), transparent 45%), radial-gradient(circle at 80% 75%, rgb(var(--brand-primary-rgb) / .5), transparent 50%)", backgroundColor: "var(--secondary)" }} />
              <div className="absolute inset-0 opacity-[.15]" style={{ backgroundImage: "radial-gradient(currentColor 1.5px, transparent 1.5px)", backgroundSize: "22px 22px" }} />
              <div className="absolute bottom-7 left-5 right-5 flex items-end justify-between lg:bottom-10 lg:left-auto lg:right-10">
                <div className="rounded-xl border border-border bg-card/95 p-4 shadow-lg backdrop-blur">
                  <p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.17em] text-accent"><span className="size-2 rounded-full bg-accent" />{text("home.hero.card_label")}</p>
                  <p className="mt-1 font-display text-xl font-bold">{text("home.hero.card_title")}</p>
                </div>
                <div className="grid size-14 place-items-center rounded-full bg-primary text-primary-foreground shadow-xl"><Compass size={24} /></div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-b border-border bg-primary text-primary-foreground">
          <div className="mx-auto flex max-w-[1320px] flex-wrap items-center justify-between gap-5 px-5 py-5 lg:px-10">
            <p className="flex items-center gap-2 text-sm font-semibold"><Sparkles size={15} className="text-accent" /> {text("home.trust.title")}</p>
            <div className="flex flex-wrap gap-x-7 gap-y-2 text-xs font-bold uppercase tracking-[.15em] opacity-80">{trustItems.map((item) => <span key={item}>{item}</span>)}</div>
          </div>
        </section>

        <section id="discover" className="mx-auto max-w-[1320px] px-5 py-16 lg:px-10 lg:py-24">
          <div className="grid gap-12 lg:grid-cols-[.3fr_.7fr] lg:gap-20">
            <div>
              <p className="text-xs font-bold uppercase tracking-[.2em] text-accent">{text("home.browse.eyebrow")}</p>
              <h2 className="mt-5 max-w-xs font-display text-4xl font-bold leading-[.94] tracking-[-.05em] sm:text-5xl">{text("home.browse.title")}</h2>
              <p className="mt-6 max-w-xs text-sm leading-6 text-muted-foreground">{text("home.browse.description")}</p>
              <div className="mt-10 hidden rounded-xl bg-accent/15 p-5 lg:block">
                <Check size={22} className="text-accent" />
                <p className="mt-10 font-display text-2xl font-bold leading-tight">{text("home.browse.callout_title")}</p>
                <p className="mt-3 text-sm leading-5 text-muted-foreground">{text("home.browse.callout_description")}</p>
                <Link href="/find-providers" className="mt-6 inline-flex items-center gap-2 text-sm font-bold underline underline-offset-4">{text("home.browse.callout_action")} <ChevronRight size={15} /></Link>
              </div>
            </div>
            <div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <label className="flex flex-1 items-center gap-3 rounded-xl border border-border bg-card px-4 py-3.5 shadow-sm">
                  <Search size={18} className="text-muted-foreground" />
                  <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={text("home.search.placeholder")} className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground" />
                </label>
                <button onClick={() => toast(text("home.search.filters"), { description: text("home.search.filter_description") })} className="inline-flex items-center justify-center gap-2 rounded-xl border border-border px-5 py-3.5 text-sm font-bold">{text("home.search.filters")}</button>
              </div>
              <div className="mt-5 flex gap-2 overflow-x-auto pb-2">
                <button onClick={() => setActiveCategory(text("home.filters.all_services"))} className={`whitespace-nowrap rounded-full px-4 py-2.5 text-xs font-bold transition ${activeCategory === text("home.filters.all_services") ? "bg-primary text-primary-foreground" : "border border-border bg-card text-muted-foreground"}`}>{text("home.filters.all_services")}</button>
                {categories.map((category) => <button key={category.id} onClick={() => setActiveCategory(category.name)} className={`whitespace-nowrap rounded-full px-4 py-2.5 text-xs font-bold transition ${activeCategory === category.name ? "bg-primary text-primary-foreground" : "border border-border bg-card text-muted-foreground"}`}>{category.name}</button>)}
              </div>
              <div className="mt-8 grid gap-4 sm:grid-cols-2">{filtered.map((service) => <ServiceCard key={service.id} service={service} onOpen={setSelected} />)}</div>
              {filtered.length === 0 && <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center"><p className="font-display text-2xl font-bold">{text("home.search.empty_title")}</p><p className="mt-2 text-sm text-muted-foreground">{text("home.search.empty_description")}</p></div>}
            </div>
          </div>
        </section>

        <section className="overflow-hidden bg-secondary text-secondary-foreground">
          <div className="mx-auto grid max-w-[1320px] items-center gap-10 px-5 py-16 lg:grid-cols-[.8fr_1.2fr] lg:px-10 lg:py-24">
            <div>
              <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.2em] text-accent"><span className="size-2 rounded-full bg-accent" />{text("home.cta.eyebrow")}</p>
              <h2 className="mt-5 max-w-lg font-display text-4xl font-bold leading-[.94] tracking-[-.05em] sm:text-5xl">{text("home.cta.title")}</h2>
              <p className="mt-6 max-w-md text-base leading-7 opacity-80">{text("home.cta.description")}</p>
              <Link href="/register" className="mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3.5 text-sm font-bold text-primary-foreground">{text("home.cta.action")} <ArrowUpRight size={17} /></Link>
            </div>
            <div className="relative min-h-[260px] overflow-hidden rounded-xl border border-border bg-card p-3 shadow-lg">
              <div className="relative flex size-full min-h-[220px] items-center justify-center rounded-lg bg-background">
                <div className="grid grid-cols-3 gap-3 p-6 opacity-90">{Array.from({ length: 9 }).map((_, i) => <span key={i} className="size-8 rounded-full bg-accent/15" />)}</div>
                <div className="absolute bottom-5 left-5 right-5 rounded-xl bg-card/95 p-4 shadow">
                  <p className="text-[10px] font-bold uppercase tracking-[.17em] text-accent">{text("home.cta.note_label")}</p>
                  <p className="mt-2 font-display text-lg font-bold leading-tight">{text("home.cta.note_text")}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <footer className="bg-background">
          <div className="mx-auto flex max-w-[1320px] flex-col gap-8 px-5 py-12 sm:flex-row sm:items-end sm:justify-between lg:px-10">
            <div><Logo /><p className="mt-4 max-w-xs text-sm leading-6 text-muted-foreground">{text("footer.description")}</p></div>
            <div className="flex flex-wrap gap-x-6 gap-y-3 text-xs font-bold uppercase tracking-[.15em] text-muted-foreground">
              <button onClick={() => comingSoon(text("footer.about"))}>{text("footer.about")}</button>
              <button onClick={() => comingSoon(text("footer.safety"))}>{text("footer.safety")}</button>
              <button onClick={() => comingSoon(text("footer.support"))}>{text("footer.support")}</button>
            </div>
          </div>
        </footer>
      </main>

      <div className="fixed bottom-4 left-1/2 z-30 flex -translate-x-1/2 items-center gap-1 rounded-full border border-border bg-card/95 p-1.5 shadow-2xl backdrop-blur md:hidden">
        <a href="#top" className="grid size-11 place-items-center rounded-full bg-accent text-accent-foreground" aria-label={text("navigation.home")}><Compass size={18} /></a>
        <a href="#discover" className="grid size-11 place-items-center rounded-full text-muted-foreground" aria-label={text("navigation.find_service")}><Search size={18} /></a>
        <Link href="/find-providers" className="grid size-11 place-items-center rounded-full text-muted-foreground" aria-label={text("navigation.providers_near_me")}><UserRound size={18} /></Link>
      </div>

      {selected && <div className="fixed inset-0 z-50 grid place-items-center bg-foreground/40 p-5 backdrop-blur-sm" role="dialog" aria-modal="true">
        <div className="relative max-h-[90vh] w-full max-w-lg overflow-auto rounded-xl bg-card p-7 shadow-2xl">
          <button onClick={() => setSelected(null)} className="absolute right-5 top-5 grid size-9 place-items-center rounded-full border border-border" aria-label={text("system.actions.close")}><X size={16} /></button>
          <div className="mb-8 grid size-14 place-items-center rounded-full bg-accent/20"><span className="font-display text-2xl font-bold text-accent">{selected.category_name.charAt(0)}</span></div>
          <p className="text-xs font-bold uppercase tracking-[.18em] text-accent">{selected.category_name}</p>
          <h2 className="mt-3 pr-8 font-display text-3xl font-bold leading-[.98] tracking-[-.04em] sm:text-4xl">{selected.name}</h2>
          <p className="mt-5 text-sm leading-6 text-muted-foreground">{selected.description || ""}</p>
          <Link href={`/find-providers?service=${selected.id}`} onClick={() => setSelected(null)} className="mt-7 flex w-full items-center justify-center gap-2 rounded-full bg-primary px-5 py-4 text-sm font-bold text-primary-foreground">{text("home.service_modal.find_providers")} <ArrowUpRight size={17} /></Link>
        </div>
      </div>}
    </div>
  );
}
