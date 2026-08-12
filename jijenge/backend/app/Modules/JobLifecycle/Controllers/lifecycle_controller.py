from app.Modules.JobLifecycle.Services.lifecycle_service import LifecycleService
class LifecycleController:
    def __init__(self): self.service=LifecycleService()
    def transition(self,*args): return self.service.transition(*args)
    def events(self,*args): return self.service.events(*args)
