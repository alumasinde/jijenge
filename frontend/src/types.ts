export interface Branding {
  app_name?: string; short_name?: string; tagline?: string; logo_url?: string | null;
  primary_color?: string; secondary_color?: string; accent_color?: string;
  background_color?: string; surface_color?: string; text_color?: string;
  font_family?: string; border_radius?: string;
}
export interface ServiceCategory { id: number; code: string; name: string; description?: string | null }
export interface Service { id: number; category_id?: number; category_code?: string; category_name?: string; code: string; name: string; description?: string | null }
export interface ServiceList { items: Service[]; total: number }
