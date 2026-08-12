
from fastapi import APIRouter

from app.database import db_connection

router=APIRouter(prefix="/system",tags=["System"])


@router.get("/health")
def health():
    return {"status":"ok"}


@router.get("/ready")
def readiness():
    try:
        with db_connection() as connection:
            cursor=connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return {"status":"ready","database":"ok"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503,detail="Service is not ready")
