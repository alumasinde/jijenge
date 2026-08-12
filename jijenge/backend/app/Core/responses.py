def success_response(data=None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: str = "ERROR") -> dict:
    return {"success": False, "message": message, "code": code}
