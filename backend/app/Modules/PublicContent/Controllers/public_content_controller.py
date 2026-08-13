from app.Modules.PublicContent.Services.public_content_service import PublicContentService


class PublicContentController:
    def __init__(self):
        self.service = PublicContentService()

    def get_public(self, locale):
        return self.service.get_public(locale)

    def list_admin(self, locale, active_only, search):
        return self.service.list_admin(locale, active_only, search)

    def create(self, data):
        return self.service.create(data)

    def update(self, content_id, data):
        return self.service.update(content_id, data)

    def delete(self, content_id):
        return self.service.delete(content_id)
