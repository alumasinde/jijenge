from app.Modules.Services.Services.service_service import ServiceService


class ServiceController:
    def __init__(self):
        self.service = ServiceService()

    def list_categories(self):
        return self.service.list_categories()

    def list_services(self, category_id: int | None = None):
        return self.service.list_services(category_id)
