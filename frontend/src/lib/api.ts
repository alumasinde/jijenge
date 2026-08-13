// Thin fetch wrapper over the Jijenge backend (FastAPI, prefix /api/v1).
// Types below mirror the backend's actual pydantic response models -
// see app/Modules/*/schema.py in the backend repo. Fields that don't
// exist on the real API (price, rating, provider name on a bare
// service, etc.) are intentionally not modeled here: the Services
// endpoint is a catalog of service *types*, not individual listings.
// Provider-level browsing goes through getProviderDiscovery() instead.

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const ACCESS_TOKEN_KEY = "jijenge_access_token";
const REFRESH_TOKEN_KEY = "jijenge_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.detail || body?.message || detail;
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Branding

export type Branding = {
  id: number;
  brand_code: string;
  app_name: string;
  short_name: string;
  tagline: string | null;
  logo_url: string | null;
  logo_dark_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string;
  surface_color: string;
  text_color: string;
  muted_color: string;
  border_color: string;
  success_color: string;
  warning_color: string;
  danger_color: string;
  info_color: string;
  font_family: string;
  border_radius: string;
  dark_mode_enabled: boolean;
  dark_theme: Record<string, unknown> | null;
  is_active: boolean;
};

export async function getBranding(): Promise<Branding> {
  return request<Branding>("/branding");
}

// ---------------------------------------------------------------------------
// Services (catalog of service types, e.g. "Plumbing", "Catering")

export type ServiceCategory = {
  id: number;
  code: string;
  name: string;
  description: string | null;
};

export type Service = {
  id: number;
  category_id: number;
  category_code: string;
  category_name: string;
  code: string;
  name: string;
  description: string | null;
};

export async function getCategories(): Promise<ServiceCategory[]> {
  return request<ServiceCategory[]>("/services/categories");
}

export async function getServices(): Promise<Service[]> {
  const result = await request<{ items: Service[]; total: number }>("/services");
  return result.items;
}


// ---------------------------------------------------------------------------
// Public site content (database-backed CMS values)

export type PublicContentValue = string | number | boolean | null | PublicContentValue[] | { [key: string]: PublicContentValue };

export type PublicContentItem = {
  key: string;
  value: PublicContentValue;
  locale: string;
  content_type: string;
  sort_order: number;
};

export type PublicContentResponse = {
  locale: string;
  items: PublicContentItem[];
};

export async function getPublicContent(locale = "en-KE"): Promise<Record<string, PublicContentValue>> {
  const result = await request<PublicContentResponse>(`/public/content?locale=${encodeURIComponent(locale)}`);
  return Object.fromEntries(result.items.map((item) => [item.key, item.value]));
}

// ---------------------------------------------------------------------------
// Public content CMS (admin)

export type AdminPublicContentItem = {
  id: number;
  content_key: string;
  locale: string;
  content_type: "text" | "json" | "number" | "boolean";
  value: PublicContentValue;
  is_active: boolean;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
};

export type PublicContentWrite = {
  content_key: string;
  locale: string;
  content_type: "text" | "json" | "number" | "boolean";
  content_value: PublicContentValue;
  is_active: boolean;
  sort_order: number;
};

export async function getAdminPublicContent(params: { locale?: string; activeOnly?: boolean; search?: string } = {}): Promise<AdminPublicContentItem[]> {
  const query = new URLSearchParams();
  if (params.locale) query.set("locale", params.locale);
  if (params.activeOnly) query.set("active_only", "true");
  if (params.search) query.set("search", params.search);
  return request<AdminPublicContentItem[]>(`/admin/public-content?${query.toString()}`);
}

export async function createPublicContent(payload: PublicContentWrite): Promise<AdminPublicContentItem> {
  return request<AdminPublicContentItem>("/admin/public-content", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updatePublicContent(id: number, payload: PublicContentWrite): Promise<AdminPublicContentItem> {
  return request<AdminPublicContentItem>(`/admin/public-content/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deletePublicContent(id: number): Promise<void> {
  return request<void>(`/admin/public-content/${id}`, { method: "DELETE" });
}

// ---------------------------------------------------------------------------
// Providers (people/businesses offering services, discoverable by location)

export type ProviderDiscoveryResult = {
  provider_id: number;
  business_name: string | null;
  professional_title: string | null;
  bio: string | null;
  years_experience: number | null;
  is_verified: boolean;
  distance_km: number;
  services: string[];
};

export type DiscoverProvidersParams = {
  latitude: number;
  longitude: number;
  serviceId?: number;
  radiusKm?: number;
  limit?: number;
  verifiedOnly?: boolean;
};

export async function discoverProviders(params: DiscoverProvidersParams): Promise<ProviderDiscoveryResult[]> {
  const query = new URLSearchParams({
    latitude: String(params.latitude),
    longitude: String(params.longitude),
  });
  if (params.serviceId) query.set("service_id", String(params.serviceId));
  if (params.radiusKm) query.set("radius_km", String(params.radiusKm));
  if (params.limit) query.set("limit", String(params.limit));
  if (params.verifiedOnly) query.set("verified_only", "true");

  return request<ProviderDiscoveryResult[]>(`/providers/discover?${query.toString()}`);
}

// ---------------------------------------------------------------------------
// Auth

export type AuthUser = {
  id: number;
  first_name?: string;
  last_name?: string;
  email?: string | null;
  phone?: string | null;
  [key: string]: unknown;
};

export type AuthResult = {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export async function login(identifier: string, password: string): Promise<AuthResult> {
  const result = await request<AuthResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
  });
  setTokens(result.access_token, result.refresh_token);
  return result;
}

export type RegisterInput = {
  firstName: string;
  lastName: string;
  email?: string;
  phone?: string;
  password: string;
};

export async function register(input: RegisterInput): Promise<AuthResult> {
  const result = await request<AuthResult>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      first_name: input.firstName,
      last_name: input.lastName,
      email: input.email || undefined,
      phone: input.phone || undefined,
      password: input.password,
    }),
  });
  setTokens(result.access_token, result.refresh_token);
  return result;
}

export async function logout(): Promise<void> {
  try {
    await request<void>("/auth/logout", { method: "POST" });
  } finally {
    clearTokens();
  }
}

export async function getCurrentUser(): Promise<AuthUser> {
  return request<AuthUser>("/auth/me");
}

// ---------------------------------------------------------------------------
// Presentation helpers

export function serviceCategory(service: Service) {
  return service.category_name;
}

export function serviceTitle(service: Service) {
  return service.name;
}
