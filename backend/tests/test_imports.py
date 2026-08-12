import unittest


class ImportTests(unittest.TestCase):
    def test_application_routes_import(self):
        from app.api.v1.routes import router
        self.assertGreater(len(router.routes),0)

    def test_provider_abstraction_imports(self):
        from app.Modules.Payments.Providers.registry import PaymentProviderRegistry
        self.assertTrue(PaymentProviderRegistry)


if __name__=="__main__":
    unittest.main()
