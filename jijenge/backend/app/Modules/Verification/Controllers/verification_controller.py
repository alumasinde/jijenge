from app.Modules.Verification.Services.verification_service import VerificationService


class VerificationController:
    def __init__(self):
        self.service = VerificationService()

    def create_request(self, user_id, verification_type_code):
        return self.service.create_request(user_id, verification_type_code)

    def add_document(self, user_id, request_id, data):
        return self.service.add_document(user_id, request_id, data)

    def list_requests(self, user_id):
        return self.service.list_requests(user_id)
