from app.Modules.Trust.Services.trust_service import TrustService


class TrustController:
    def __init__(self):
        self.service = TrustService()

    def create_report(self, user_id, data):
        return self.service.create_report(user_id, data)
