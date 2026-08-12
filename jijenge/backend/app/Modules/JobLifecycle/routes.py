from fastapi import APIRouter,Depends,Request
from app.config import settings
from app.Core.auth import AuthenticatedUser,require_role
from app.Core.rate_limit import enforce_rate_limit
from app.Modules.JobLifecycle.Controllers.lifecycle_controller import LifecycleController
from app.Modules.JobLifecycle.schema import JobTransitionRequest,JobLifecycleResponse,JobEventResponse
router=APIRouter(prefix="/jobs",tags=["Job Lifecycle"]);controller=LifecycleController()

def transition(request,job_id,data,user,role,target,limit_key):
    enforce_rate_limit(request,limit_key,settings.auth_rate_limit_per_minute)
    return controller.transition(user.id,role,job_id,target,data)

@router.post("/{job_id}/cancel",response_model=JobLifecycleResponse)
def customer_cancel(request:Request,job_id:int,data:JobTransitionRequest,user:AuthenticatedUser=Depends(require_role("CUSTOMER"))): return transition(request,job_id,data,user,"CUSTOMER","CANCELLED","jobs:cancel")
@router.post("/{job_id}/on-the-way",response_model=JobLifecycleResponse)
def on_way(request:Request,job_id:int,data:JobTransitionRequest,user:AuthenticatedUser=Depends(require_role("PROVIDER"))): return transition(request,job_id,data,user,"PROVIDER","ON_THE_WAY","jobs:on-the-way")
@router.post("/{job_id}/start",response_model=JobLifecycleResponse)
def start(request:Request,job_id:int,data:JobTransitionRequest,user:AuthenticatedUser=Depends(require_role("PROVIDER"))): return transition(request,job_id,data,user,"PROVIDER","IN_PROGRESS","jobs:start")
@router.post("/{job_id}/complete",response_model=JobLifecycleResponse)
def complete(request:Request,job_id:int,data:JobTransitionRequest,user:AuthenticatedUser=Depends(require_role("PROVIDER"))): return transition(request,job_id,data,user,"PROVIDER","COMPLETED","jobs:complete")
@router.post("/{job_id}/provider-cancel",response_model=JobLifecycleResponse)
def provider_cancel(request:Request,job_id:int,data:JobTransitionRequest,user:AuthenticatedUser=Depends(require_role("PROVIDER"))): return transition(request,job_id,data,user,"PROVIDER","CANCELLED","jobs:provider-cancel")
@router.get("/{job_id}/events",response_model=list[JobEventResponse])
def customer_events(job_id:int,user:AuthenticatedUser=Depends(require_role("CUSTOMER"))): return controller.events(user.id,"CUSTOMER",job_id)
@router.get("/{job_id}/provider-events",response_model=list[JobEventResponse])
def provider_events(job_id:int,user:AuthenticatedUser=Depends(require_role("PROVIDER"))): return controller.events(user.id,"PROVIDER",job_id)
