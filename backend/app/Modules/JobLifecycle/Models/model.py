from dataclasses import dataclass
@dataclass(frozen=True)
class JobLifecycle:
    job_id:int
    status_code:str
    assigned_provider_id:int|None
