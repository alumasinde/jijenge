import { useEffect, useState } from "react";
import { Link, useSearch } from "wouter";
import { BadgeCheck, Compass, Loader2, MapPin, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { discoverProviders, getServices, type ProviderDiscoveryResult, type Service } from "@/lib/api";
import { useBranding } from "@/contexts/BrandingContext";

type LocationState = { latitude: number; longitude: number } | null;

export default function FindProviders() {
  const { branding } = useBranding();
  const locationSearch = useSearch();
  const [services, setServices] = useState<Service[]>([]);
  const [serviceId, setServiceId] = useState<number | "">("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [location, setLocation] = useState<LocationState>(null);
  const [locating, setLocating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ProviderDiscoveryResult[]>([]);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const preselected = new URLSearchParams(locationSearch).get("service");
    if (preselected) setServiceId(Number(preselected));
  }, [locationSearch]);

  useEffect(() => {
    getServices()
      .then(setServices)
      .catch(() => toast.error("Couldn't load the service list"));
  }, []);

  function useMyLocation() {
    if (!navigator.geolocation) {
      toast.error("Your browser doesn't support location. Enter it manually is coming soon.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({ latitude: position.coords.latitude, longitude: position.coords.longitude });
        setLocating(false);
      },
      () => {
        toast.error("Couldn't get your location. Check your browser's permission for this site.");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function search() {
    if (!location) {
      toast.error("Share your location first so we can find nearby providers");
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      const found = await discoverProviders({
        latitude: location.latitude,
        longitude: location.longitude,
        serviceId: serviceId || undefined,
        verifiedOnly,
        radiusKm: 25,
      });
      setResults(found);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't search right now");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border px-5 py-5 lg:px-10">
        <div className="mx-auto flex max-w-[1100px] items-center justify-between">
          <Link href="/" className="text-sm font-bold text-muted-foreground transition hover:text-foreground">&larr; Back to {branding.short_name}</Link>
        </div>
      </header>

      <main className="mx-auto max-w-[1100px] px-5 py-12 lg:px-10 lg:py-16">
        <p className="text-xs font-bold uppercase tracking-[.2em] text-accent">Find providers near you</p>
        <h1 className="mt-4 max-w-lg font-display text-5xl font-bold leading-[.95] tracking-[-.05em]">Who's nearby, right now.</h1>
        <p className="mt-5 max-w-md text-sm leading-6 text-muted-foreground">Share your location and we'll surface providers working close to you, closest first.</p>

        <div className="mt-10 grid gap-4 rounded-2xl border border-border bg-card p-5 sm:grid-cols-[1fr_auto]">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <label htmlFor="service" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Service (optional)</label>
              <select
                id="service"
                value={serviceId}
                onChange={(e) => setServiceId(e.target.value ? Number(e.target.value) : "")}
                className="rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none transition focus:border-primary"
              >
                <option value="">Any service</option>
                {services.map((service) => (
                  <option key={service.id} value={service.id}>{service.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end gap-2 pb-1">
              <label className="flex items-center gap-2 text-sm font-semibold">
                <input type="checkbox" checked={verifiedOnly} onChange={(e) => setVerifiedOnly(e.target.checked)} className="size-4 rounded border-border" />
                Verified providers only
              </label>
            </div>
          </div>

          <div className="flex flex-col justify-end gap-2 sm:items-end">
            <button
              onClick={useMyLocation}
              disabled={locating}
              className="inline-flex items-center justify-center gap-2 rounded-full border border-border px-4 py-3 text-xs font-bold uppercase tracking-[.12em] transition hover:bg-muted disabled:opacity-60"
            >
              {locating ? <Loader2 size={15} className="animate-spin" /> : <MapPin size={15} />}
              {location ? "Location set" : "Use my location"}
            </button>
            <button
              onClick={search}
              disabled={loading || !location}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-bold text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Compass size={16} />}
              Search nearby
            </button>
          </div>
        </div>

        <div className="mt-10 grid gap-4">
          {searched && !loading && results.length === 0 && (
            <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center">
              <p className="font-display text-2xl font-bold">No one nearby yet.</p>
              <p className="mt-2 text-sm text-muted-foreground">Try a wider service category or check back soon as more providers join.</p>
            </div>
          )}

          {results.map((provider) => (
            <div key={provider.provider_id} className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-display text-xl font-bold">{provider.business_name || provider.professional_title || "Independent provider"}</h3>
                  {provider.is_verified && <BadgeCheck size={16} className="text-info" aria-label="Verified" />}
                </div>
                {provider.professional_title && provider.business_name && (
                  <p className="mt-0.5 text-sm text-muted-foreground">{provider.professional_title}</p>
                )}
                {provider.bio && <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground line-clamp-2">{provider.bio}</p>}
                {provider.services.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {provider.services.map((name) => (
                      <span key={name} className="rounded-full border border-border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[.08em] text-muted-foreground">{name}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex shrink-0 flex-col items-start gap-1 text-sm sm:items-end">
                <span className="flex items-center gap-1.5 font-bold"><MapPin size={14} /> {provider.distance_km.toFixed(1)} km away</span>
                {provider.years_experience != null && (
                  <span className="flex items-center gap-1.5 text-muted-foreground"><ShieldCheck size={14} /> {provider.years_experience} yrs experience</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
