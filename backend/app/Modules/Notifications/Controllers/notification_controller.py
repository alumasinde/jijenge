from app.Modules.Notifications.Services.notification_service import NotificationService


class NotificationController:
    def __init__(self):
        self.service = NotificationService()

    def list_for_user(self, user_id, limit, offset):
        return self.service.list_for_user(user_id, limit, offset)

    def mark_read(self, user_id, notification_id):
        return self.service.mark_read(user_id, notification_id)

    def mark_all_read(self, user_id):
        return self.service.mark_all_read(user_id)

    def register_device(self, user_id, data):
        return self.service.register_device(user_id, data)

    def deactivate_device(self, user_id, token):
        return self.service.deactivate_device(user_id, token)
