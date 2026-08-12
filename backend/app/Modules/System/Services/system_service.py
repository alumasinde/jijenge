from fastapi import HTTPException, status

from app.Modules.System.Repositories.system_repository import SystemRepository


class SystemService:
    def __init__(self):
        self.repository = SystemRepository()

    def public_settings(self):
        return self.repository.list_settings(public_only=True)

    def all_settings(self):
        return self.repository.list_settings(public_only=False)

    def get_public_setting(self, key):
        setting = self.repository.get_setting(key, public_only=True)
        if not setting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
        return setting

    def upsert(self, key, data):
        existing = self.repository.get_setting(key)
        if existing and not existing["is_editable"]:
            raise HTTPException(status_code=403, detail="This setting is not editable")

        value = data.value
        value_type = data.value_type
        if value_type == "string" and not isinstance(value, str):
            raise HTTPException(status_code=422, detail="value must be a string")
        if value_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            raise HTTPException(status_code=422, detail="value must be an integer")
        if value_type == "decimal" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            raise HTTPException(status_code=422, detail="value must be numeric")
        if value_type == "boolean" and not isinstance(value, bool):
            raise HTTPException(status_code=422, detail="value must be boolean")
        return self.repository.upsert_setting(key, data.model_dump())

    def delete(self, key):
        existing = self.repository.get_setting(key)
        if not existing:
            raise HTTPException(status_code=404, detail="Setting not found")
        if not existing["is_editable"]:
            raise HTTPException(status_code=403, detail="This setting is not editable")
        if not self.repository.delete_setting(key):
            raise HTTPException(status_code=404, detail="Setting not found")
        return {"deleted": True, "setting_key": key}
