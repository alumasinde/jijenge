from app.Modules.Availability.Repositories.availability_repository import (
    AvailabilityRepository,
)


class AvailabilityController:
    def __init__(self):
        self.repository = AvailabilityRepository()

    def add_rule(self, provider_id, data):
        return self.repository.add_rule(provider_id, data)

    def list_rules(self, provider_id):
        return self.repository.list_rules(provider_id)

    def add_exception(self, provider_id, data):
        return self.repository.add_exception(provider_id, data)

    def list_exceptions(self, provider_id, from_date, to_date):
        return self.repository.list_exceptions(
            provider_id, from_date, to_date
        )

    def get_preferences(self, provider_id):
        return self.repository.get_preferences(provider_id)

    def upsert_preferences(self, provider_id, data):
        return self.repository.upsert_preferences(provider_id, data)
