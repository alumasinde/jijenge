from app.Modules.Payments.Services.cash_service import CashService


class CashController:
    def __init__(self):
        self.service = CashService()

    def confirm(self, **kwargs):
        return self.service.confirm(**kwargs)
