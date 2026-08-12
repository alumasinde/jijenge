import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.Modules.Branding.schema import BrandingUpdateRequest
from app.Modules.System.schema import SystemSettingUpsertRequest


class SystemBrandingTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_routes_are_registered(self):
        paths = {route.path for route in self.client.app.routes}
        self.assertIn("/api/v1/system/health", paths)
        self.assertIn("/api/v1/system/ready", paths)
        self.assertIn("/api/v1/system/settings", paths)
        self.assertIn("/api/v1/system/admin/settings/{setting_key}", paths)
        self.assertIn("/api/v1/branding", paths)

    def test_health_is_public(self):
        response = self.client.get("/api/v1/system/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("app.Modules.Branding.Repositories.branding_repository.db_connection")
    def test_branding_repository_normalizes_json_and_flags(self, mock_connection):
        class Cursor:
            def execute(self, *args): pass
            def fetchone(self):
                return {
                    "id": 1,
                    "brand_code": "default",
                    "app_name": "Jijenge",
                    "short_name": "Jijenge",
                    "tagline": "Test",
                    "logo_url": None,
                    "logo_dark_url": None,
                    "favicon_url": None,
                    "primary_color": "#2563EB",
                    "secondary_color": "#1E40AF",
                    "accent_color": "#F59E0B",
                    "background_color": "#F8FAFC",
                    "surface_color": "#FFFFFF",
                    "text_color": "#0F172A",
                    "muted_color": "#64748B",
                    "border_color": "#E2E8F0",
                    "success_color": "#16A34A",
                    "warning_color": "#D97706",
                    "danger_color": "#DC2626",
                    "info_color": "#0284C7",
                    "font_family": "Inter",
                    "border_radius": "0.75rem",
                    "dark_mode_enabled": 1,
                    "dark_theme_json": '{"background":"#0F172A"}',
                    "is_active": 1,
                    "created_at": "2026-08-12T00:00:00",
                    "updated_at": "2026-08-12T00:00:00",
                }
            def close(self): pass
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def cursor(self, **kwargs): return Cursor()
        mock_connection.return_value = Connection()

        from app.Modules.Branding.Repositories.branding_repository import BrandingRepository
        row = BrandingRepository().get_active()
        self.assertEqual(row["dark_theme"], {"background": "#0F172A"})
        self.assertTrue(row["is_active"])
        self.assertTrue(row["dark_mode_enabled"])

    def test_branding_schema_rejects_invalid_color(self):
        with self.assertRaises(ValueError):
            BrandingUpdateRequest(
                app_name="Jijenge",
                short_name="Jijenge",
                primary_color="red",
            )

    def test_system_setting_schema_rejects_unknown_type(self):
        with self.assertRaises(ValueError):
            SystemSettingUpsertRequest(value="x", value_type="secret")


if __name__ == "__main__":
    unittest.main()
