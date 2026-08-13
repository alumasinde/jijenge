// Pulls brand identity (colors, font, radius, logo, copy) from the
// backend's /branding endpoint and applies it live as CSS custom
// properties, so the whole app re-themes itself from one source of
// truth instead of hardcoded values scattered across components.
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getBranding, type Branding } from "@/lib/api";

// Used only until the real branding loads (or if the request fails),
// so the app never flashes unstyled. Deliberately not a copy of any
// single well-known "AI generated" palette (warm-cream-plus-terracotta,
// near-black-plus-acid-accent, or default SaaS blue) - just a calm
// neutral placeholder that gets replaced the moment real data arrives.
const FALLBACK_BRANDING: Branding = {
  id: 0,
  brand_code: "default",
  app_name: "Jijenge",
  short_name: "Jijenge",
  tagline: "Find trusted services and get things done.",
  logo_url: null,
  logo_dark_url: null,
  favicon_url: null,
  primary_color: "#1E211C",
  secondary_color: "#3A3B2D",
  accent_color: "#6D6B60",
  background_color: "#F5F4F0",
  surface_color: "#FFFFFF",
  text_color: "#1E211C",
  muted_color: "#6D6B60",
  border_color: "#E2E1DC",
  success_color: "#16A34A",
  warning_color: "#D97706",
  danger_color: "#DC2626",
  info_color: "#0284C7",
  font_family: "DM Sans, ui-sans-serif, system-ui, sans-serif",
  border_radius: "0.75rem",
  dark_mode_enabled: true,
  dark_theme: null,
  is_active: true,
};

interface BrandingContextType {
  branding: Branding;
  loading: boolean;
  error: boolean;
}

const BrandingContext = createContext<BrandingContextType | undefined>(undefined);

// Converts a #RRGGBB hex color to an "R G B" triple so Tailwind's
// `bg-primary/50` style opacity modifiers keep working (they need a
// space-separated channel value, not a hex string, behind the var()).
function hexToRgbTriple(hex: string): string | null {
  const match = /^#([0-9a-f]{6})$/i.exec(hex.trim());
  if (!match) return null;
  const int = parseInt(match[1], 16);
  const r = (int >> 16) & 255;
  const g = (int >> 8) & 255;
  const b = int & 255;
  return `${r} ${g} ${b}`;
}

const COLOR_VAR_MAP: Record<string, keyof Branding> = {
  "--brand-primary": "primary_color",
  "--brand-secondary": "secondary_color",
  "--brand-accent": "accent_color",
  "--brand-background": "background_color",
  "--brand-surface": "surface_color",
  "--brand-text": "text_color",
  "--brand-muted": "muted_color",
  "--brand-border": "border_color",
  "--brand-success": "success_color",
  "--brand-warning": "warning_color",
  "--brand-danger": "danger_color",
  "--brand-info": "info_color",
};

let injectedFontHref: string | null = null;

// Loads the first font family named in a CSS font-family value from
// Google Fonts, if it isn't a system font already. Safe to call
// repeatedly; it swaps out the previous link rather than stacking them.
function loadBrandFont(fontFamily: string) {
  const firstFamily = fontFamily.split(",")[0]?.trim().replace(/^["']|["']$/g, "");
  if (!firstFamily) return;

  const systemFonts = new Set(["system-ui", "ui-sans-serif", "ui-serif", "sans-serif", "serif", "monospace"]);
  if (systemFonts.has(firstFamily.toLowerCase())) return;

  const family = firstFamily.replace(/\s+/g, "+");
  const href = `https://fonts.googleapis.com/css2?family=${family}:wght@400;500;600;700;800&display=swap`;
  if (injectedFontHref === href) return;

  const existing = document.getElementById("brand-font-link");
  if (existing) existing.remove();

  const link = document.createElement("link");
  link.id = "brand-font-link";
  link.rel = "stylesheet";
  link.href = href;
  document.head.appendChild(link);
  injectedFontHref = href;
}

function applyBranding(branding: Branding, isDark: boolean) {
  const root = document.documentElement;

  const overrides =
    isDark && branding.dark_mode_enabled && branding.dark_theme
      ? (branding.dark_theme as Partial<Branding>)
      : null;

  for (const [cssVar, field] of Object.entries(COLOR_VAR_MAP)) {
    const value = (overrides?.[field] as string | undefined) || (branding[field] as string);
    if (!value) continue;
    root.style.setProperty(cssVar, value);
    const rgb = hexToRgbTriple(value);
    if (rgb) root.style.setProperty(`${cssVar}-rgb`, rgb);
  }

  root.style.setProperty("--brand-radius", branding.border_radius || "0.75rem");
  root.style.setProperty("--brand-font", branding.font_family);

  loadBrandFont(branding.font_family);

  if (branding.favicon_url) {
    let favicon = document.querySelector<HTMLLinkElement>("link[rel='icon']");
    if (!favicon) {
      favicon = document.createElement("link");
      favicon.rel = "icon";
      document.head.appendChild(favicon);
    }
    favicon.href = branding.favicon_url;
  }

  if (branding.app_name) {
    document.title = branding.tagline
      ? `${branding.app_name} — ${branding.tagline}`
      : branding.app_name;
  }
}

interface BrandingProviderProps {
  children: React.ReactNode;
  isDark?: boolean;
}

export function BrandingProvider({ children, isDark = false }: BrandingProviderProps) {
  const [branding, setBranding] = useState<Branding>(FALLBACK_BRANDING);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    applyBranding(FALLBACK_BRANDING, isDark);

    getBranding()
      .then((result) => {
        if (cancelled) return;
        setBranding(result);
        applyBranding(result, isDark);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // Re-fetching on isDark change isn't needed - dark overrides are
    // re-applied below without another network round trip.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    applyBranding(branding, isDark);
  }, [branding, isDark]);

  const value = useMemo(() => ({ branding, loading, error }), [branding, loading, error]);

  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>;
}

export function useBranding() {
  const context = useContext(BrandingContext);
  if (!context) {
    throw new Error("useBranding must be used within BrandingProvider");
  }
  return context;
}
