import json

from app.database import db_connection


class BrandingRepository:
    def get_active(self):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM brandings
                WHERE brand_code = 'default' AND is_active = 1
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            cursor.close()
            return self._normalize(row)

    def upsert_default(self, data: dict):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                dark_theme = data.pop("dark_theme", None)
                cursor.execute("SELECT id FROM brandings WHERE brand_code = 'default' LIMIT 1")
                existing = cursor.fetchone()
                values = (
                    data["app_name"], data["short_name"], data.get("tagline"),
                    data.get("logo_url"), data.get("logo_dark_url"), data.get("favicon_url"),
                    data["primary_color"], data["secondary_color"], data["accent_color"],
                    data["background_color"], data["surface_color"], data["text_color"],
                    data["muted_color"], data["border_color"], data["success_color"],
                    data["warning_color"], data["danger_color"], data["info_color"],
                    data["font_family"], data["border_radius"], data["dark_mode_enabled"],
                    json.dumps(dark_theme) if dark_theme is not None else None,
                )
                if existing:
                    cursor.execute(
                        """
                        UPDATE brandings SET
                            app_name=%s, short_name=%s, tagline=%s, logo_url=%s,
                            logo_dark_url=%s, favicon_url=%s, primary_color=%s,
                            secondary_color=%s, accent_color=%s, background_color=%s,
                            surface_color=%s, text_color=%s, muted_color=%s,
                            border_color=%s, success_color=%s, warning_color=%s,
                            danger_color=%s, info_color=%s, font_family=%s,
                            border_radius=%s, dark_mode_enabled=%s, dark_theme_json=%s,
                            updated_at=CURRENT_TIMESTAMP
                        WHERE brand_code='default'
                        """,
                        values,
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO brandings (
                            brand_code, app_name, short_name, tagline, logo_url,
                            logo_dark_url, favicon_url, primary_color, secondary_color,
                            accent_color, background_color, surface_color, text_color,
                            muted_color, border_color, success_color, warning_color,
                            danger_color, info_color, font_family, border_radius,
                            dark_mode_enabled, dark_theme_json
                        ) VALUES ('default', %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        values,
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        return self.get_active()

    @staticmethod
    def _normalize(row):
        if not row:
            return None
        if isinstance(row.get("dark_theme_json"), str):
            try:
                row["dark_theme_json"] = json.loads(row["dark_theme_json"])
            except json.JSONDecodeError:
                row["dark_theme_json"] = None
        row["dark_theme"] = row.pop("dark_theme_json", None)
        row["is_active"] = bool(row["is_active"])
        row["dark_mode_enabled"] = bool(row["dark_mode_enabled"])
        return row
