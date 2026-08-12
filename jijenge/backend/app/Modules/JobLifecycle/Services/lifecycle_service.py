from fastapi import HTTPException
from app.Modules.JobLifecycle.Repositories.lifecycle_repository import LifecycleRepository
from app.Modules.JobLifecycle.schema import JobLifecycleResponse, JobEventResponse

class LifecycleService:
    def __init__(self): self.repo=LifecycleRepository()
    def transition(self,user_id,role,job_id,target,data):
        try: row=self.repo.transition(job_id,user_id,role,target,data.notes,data.cancellation_reason,data.completion_notes)
        except LookupError: raise HTTPException(404,"Job not found")
        except PermissionError: raise HTTPException(403,"You do not have access to this job")
        except ValueError as e: raise HTTPException(409,str(e))
        return JobLifecycleResponse(job_id=int(row["job_id"]),status=row["status_code"],assigned_provider_id=(int(row["assigned_provider_id"]) if row["assigned_provider_id"] is not None else None),assigned_at=row["assigned_at"],started_at=row["started_at"],completed_at=row["completed_at"],cancelled_at=row["cancelled_at"],cancellation_reason=row["cancellation_reason"],completion_notes=row["completion_notes"])
    def events(self,user_id,role,job_id):
        try: rows=self.repo.events(job_id,user_id,role)
        except LookupError: raise HTTPException(404,"Job not found")
        return [JobEventResponse(id=int(r["id"]),job_id=int(r["job_id"]),event_type=r["event_type"],actor_user_id=int(r["actor_user_id"]),from_status=r["from_status"],to_status=r["to_status"],notes=r["notes"],created_at=r["created_at"]) for r in rows]
