from app.Modules.Financials.Repositories.report_repository import FinancialReportRepository


class FinancialReportService:
    def __init__(self):
        self.repository=FinancialReportRepository()

    def summary(self):
        return {"currencies":self.repository.summary()}

    def payment_history(self,user_id,limit=50,offset=0):
        return self.repository.payment_history(user_id,limit,offset)

    def provider_statement(self,provider_id,limit=100,offset=0):
        return self.repository.provider_statement(provider_id,limit,offset)

    def exceptions(self,limit=100,offset=0):
        return self.repository.exceptions(limit,offset)

    def kpis(self):
        return self.repository.kpis()
