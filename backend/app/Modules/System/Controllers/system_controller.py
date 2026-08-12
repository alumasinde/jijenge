from app.Modules.System.Services.system_service import SystemService


class SystemController:
    def __init__(self):
        self.service = SystemService()

    def public_settings(self):
        return self.service.public_settings()

    def all_settings(self):
        return self.service.all_settings()

    def get_public_setting(self, key):
        return self.service.get_public_setting(key)

    def upsert(self, key, data):
        return self.service.upsert(key, data)

    def delete(self, key):
        return self.service.delete(key)
