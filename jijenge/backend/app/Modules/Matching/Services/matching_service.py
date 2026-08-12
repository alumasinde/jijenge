from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.Modules.Availability.Repositories.availability_repository import (
    AvailabilityRepository,
)
from app.Modules.Matching.Repositories.matching_repository import MatchingRepository
from app.Modules.Notifications.Repositories.notification_repository import NotificationRepository


class MatchingService:
    def __init__(self):
        self.repository = MatchingRepository()
        self.availability = AvailabilityRepository()
        self.notifications = NotificationRepository()

    def _score(self, candidate, rules):
        total_weight = sum(float(r["weight"]) for r in rules if float(r["weight"]) > 0)
        if total_weight <= 0:
            total_weight = 1.0

        distance = float(candidate["distance_km"])
        rating = float(candidate["rating_average"] or 0)
        experience = float(candidate["years_experience"] or 0)
        score = 0.0

        for rule in rules:
            weight = float(rule["weight"])
            if weight <= 0:
                continue
            code = rule["code"]
            if code == "DISTANCE":
                component = max(0.0, 1.0 - (distance / 50.0))
            elif code == "RATING":
                component = min(1.0, rating / 5.0)
            elif code == "VERIFICATION":
                component = 1.0 if candidate["is_verified"] else 0.0
            elif code == "AVAILABILITY":
                component = 1.0 if candidate["available_for_job"] else 0.0
            elif code == "EXPERIENCE":
                component = min(1.0, experience / 10.0)
            else:
                component = 0.0
            score += component * weight / total_weight * 100.0

        if candidate["within_service_area"]:
            score = min(100.0, score + 5.0)
        return round(score, 4)

    def _calculate(self, job, limit):
        candidates = self.repository.find_candidates(job, max(limit * 3, limit))
        target = job["preferred_start_at"]
        if target is None:
            target = datetime.now(timezone.utc) + timedelta(minutes=60)

        rules = self.repository.get_rules()
        for candidate in candidates:
            candidate["available_for_job"] = self.availability.is_available_at(
                int(candidate["provider_id"]), target
            )
            candidate["match_score"] = self._score(candidate, rules)

        candidates = [c for c in candidates if c["available_for_job"]]
        candidates.sort(
            key=lambda c: (
                -float(c["match_score"]),
                float(c["distance_km"]),
                int(c["provider_id"]),
            )
        )
        return candidates[:limit]

    def match_job(self, customer_id, job_id, limit, refresh):
        job = self.repository.get_job_context(job_id)
        if not job or int(job["customer_id"]) != customer_id:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["status_code"] != "OPEN":
            raise HTTPException(status_code=409, detail="Only open jobs can be matched")

        if not refresh:
            saved = self.repository.list_saved(job_id, limit)
            if saved:
                return saved

        selected = self._calculate(job, limit)
        self.repository.save_candidates(job_id, selected)
        return selected

    def dispatch_job(self, job_id: int, radius_km: float = 25.0, limit: int = 20):
        job = self.repository.get_job_context(job_id)
        if not job or job["status_code"] != "OPEN":
            return {"job_id": job_id, "notified_count": 0, "candidate_count": 0}

        candidates = self._calculate(job, limit)
        if not candidates:
            return {"job_id": job_id, "notified_count": 0, "candidate_count": 0}

        self.repository.save_candidates(job_id, candidates)

        notified = 0
        provider_ids = []
        for candidate in candidates:
            try:
                self.notifications.create(
                    recipient_user_id=int(candidate["user_id"]),
                    notification_type="JOB_MATCHED",
                    title="New job near you",
                    body=(
                        f"A {job['service_id']} service job may be a good match. "
                        "Open the opportunity to review the details."
                    ),
                    entity_type="JOB",
                    entity_id=job_id,
                    data={
                        "job_id": job_id,
                        "provider_id": int(candidate["provider_id"]),
                        "distance_km": float(candidate["distance_km"]),
                        "match_score": float(candidate["match_score"]),
                    },
                )
                provider_ids.append(int(candidate["provider_id"]))
                notified += 1
            except Exception:
                # One bad recipient must not prevent other candidates from being dispatched.
                continue

        self.repository.mark_notified(job_id, provider_ids)
        dispatch_key = f"job:{job_id}:radius:{radius_km}:v1"
        self.repository.create_dispatch_log(
            job_id, dispatch_key, radius_km, len(candidates), notified
        )
        return {
            "job_id": job_id,
            "candidate_count": len(candidates),
            "notified_count": notified,
        }

    def view(self, provider_user_id: int, job_id: int):
        from app.Modules.Applications.Repositories.application_repository import ApplicationRepository
        profile = ApplicationRepository().provider_profile_for_user(provider_user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        provider_id = int(profile["id"])
        row = self.repository.get_candidate(job_id, provider_id)
        if not row:
            raise HTTPException(status_code=404, detail="Match opportunity not found")
        self.repository.mark_viewed(job_id, provider_id)
        return self.repository.get_candidate(job_id, provider_id)

    def respond(self, provider_user_id, job_id, data):
        from app.Modules.Applications.Repositories.application_repository import ApplicationRepository
        profile = ApplicationRepository().provider_profile_for_user(provider_user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        try:
            row = self.repository.respond(
                job_id, int(profile["id"]), data.accepted, data.reason
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return row
