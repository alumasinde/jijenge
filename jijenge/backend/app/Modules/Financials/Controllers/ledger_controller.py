from app.Modules.Financials.Services.ledger_service import LedgerService


class LedgerController:
    def __init__(self):
        self.service = LedgerService()
