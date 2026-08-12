from app.database import db_connection


class MatchingRepository:
    def get_job_context(self, job_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    j.id,
                    j.customer_id,
                    j.service_id,
                    j.preferred_start_at,
                    j.preferred_end_at,
                    js.code AS status_code,
                    ST_Y(jl.location_point) AS latitude,
                    ST_X(jl.location_point) AS longitude
                FROM jobs j
                INNER JOIN job_statuses js ON js.id = j.status_id
                INNER JOIN job_locations jl ON jl.job_id = j.id
                WHERE j.id = %s
                LIMIT 1
                """,
                (job_id,),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def get_rules(self):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT mrt.code, mr.weight, mr.configuration_json
                FROM matching_rules mr
                INNER JOIN matching_rule_types mrt
                    ON mrt.id = mr.rule_type_id
                WHERE mr.is_active = 1
                  AND mrt.is_active = 1
                """
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows

    def find_candidates(self, job, limit: int):
        # Hard eligibility filters happen in SQL:
        # active provider, active service, accepts new jobs, distance limit,
        # and either a service area covering the job or a primary location
        # inside the provider's configured maximum distance.
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pp.id AS provider_id,
                    pp.user_id,
                    pp.business_name,
                    pp.professional_title,
                    pp.is_verified,
                    pp.years_experience,
                    COALESCE(prs.overall_rating_average, 0) AS rating_average,
                    COALESCE(prs.published_review_count, 0) AS review_count,
                    ROUND(
                        ST_Distance_Sphere(
                            pl.location_point,
                            ST_SRID(POINT(%s, %s), 4326)
                        ) / 1000,
                        3
                    ) AS distance_km,
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM provider_service_areas psa
                            WHERE psa.provider_id = pp.id
                              AND psa.is_active = 1
                              AND ST_Distance_Sphere(
                                  psa.center_point,
                                  ST_SRID(POINT(%s, %s), 4326)
                              ) <= psa.radius_km * 1000
                        ) THEN 1
                        ELSE 0
                    END AS within_service_area
                FROM provider_profiles pp
                INNER JOIN provider_statuses pst
                    ON pst.id = pp.provider_status_id
                   AND pst.code = 'ACTIVE'
                INNER JOIN provider_services ps
                    ON ps.provider_id = pp.id
                   AND ps.service_id = %s
                   AND ps.is_active = 1
                INNER JOIN provider_locations pl
                    ON pl.provider_id = pp.id
                   AND pl.is_active = 1
                   AND pl.is_primary = 1
                INNER JOIN provider_matching_preferences pmp
                    ON pmp.provider_id = pp.id
                   AND pmp.accepts_new_jobs = 1
                LEFT JOIN provider_rating_summaries prs
                    ON prs.provider_user_id = pp.user_id
                WHERE pp.user_id <> %s
                  AND ST_Distance_Sphere(
                      pl.location_point,
                      ST_SRID(POINT(%s, %s), 4326)
                  ) <= pmp.max_distance_km * 1000
                ORDER BY
                    within_service_area DESC,
                    distance_km ASC,
                    pp.is_verified DESC,
                    rating_average DESC,
                    pp.id ASC
                LIMIT %s
                """,
                (
                    job["longitude"], job["latitude"],
                    job["longitude"], job["latitude"],
                    job["service_id"],
                    job["customer_id"],
                    job["longitude"], job["latitude"],
                    limit,
                ),
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows


    def create_dispatch_log(
        self, job_id: int, dispatch_key: str, radius_km: float,
        candidate_count: int, notified_count: int
    ):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO matching_dispatch_logs
                    (
                        job_id, dispatch_key, radius_km,
                        candidate_count, notified_count
                    )
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    candidate_count = VALUES(candidate_count),
                    notified_count = VALUES(notified_count)
                """,
                (
                    job_id, dispatch_key, radius_km,
                    candidate_count, notified_count,
                ),
            )
            connection.commit()
            cursor.close()

    def get_candidate(self, job_id: int, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    jmc.id,
                    jmc.job_id,
                    jmc.provider_id,
                    pp.user_id,
                    mcs.code AS status_code,
                    jmc.notified_at,
                    jmc.viewed_at,
                    jmc.responded_at,
                    jmc.decline_reason
                FROM job_match_candidates jmc
                INNER JOIN provider_profiles pp
                    ON pp.id = jmc.provider_id
                INNER JOIN match_candidate_statuses mcs
                    ON mcs.id = jmc.status_id
                WHERE jmc.job_id = %s
                  AND jmc.provider_id = %s
                LIMIT 1
                """,
                (job_id, provider_id),
            )
            row = cursor.fetchone()
            cursor.close()
        return row

    def mark_notified(self, job_id: int, provider_ids: list[int]):
        if not provider_ids:
            return
        with db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM match_candidate_statuses WHERE code = 'NOTIFIED' LIMIT 1"
                )
                status_id = cursor.fetchone()[0]
                placeholders = ",".join(["%s"] * len(provider_ids))
                sql = """
                    UPDATE job_match_candidates
                    SET status_id = %s,
                        notified_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s
                      AND provider_id IN ({placeholders})
                    """.format(placeholders=placeholders)
                cursor.execute(sql, [status_id, job_id, *provider_ids])
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def mark_viewed(self, job_id: int, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE job_match_candidates jmc
                INNER JOIN match_candidate_statuses mcs
                    ON mcs.code = 'NOTIFIED'
                SET jmc.viewed_at = COALESCE(jmc.viewed_at, CURRENT_TIMESTAMP)
                WHERE jmc.job_id = %s
                  AND jmc.provider_id = %s
                  AND jmc.status_id = mcs.id
                """,
                (job_id, provider_id),
            )
            connection.commit()
            cursor.close()

    def respond(self, job_id: int, provider_id: int, accepted: bool, reason: str | None):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                target = "SELECTED" if accepted else "DECLINED"
                cursor.execute(
                    "SELECT id FROM match_candidate_statuses WHERE code = %s LIMIT 1",
                    (target,),
                )
                status_id = cursor.fetchone()["id"]

                cursor.execute(
                    """
                    UPDATE job_match_candidates
                    SET status_id = %s,
                        responded_at = CURRENT_TIMESTAMP,
                        decline_reason = %s
                    WHERE job_id = %s
                      AND provider_id = %s
                      AND status_id IN (
                          SELECT id FROM match_candidate_statuses
                          WHERE code IN ('ELIGIBLE', 'NOTIFIED')
                      )
                    """,
                    (status_id, reason if not accepted else None, job_id, provider_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("Match opportunity is no longer active")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

        return self.get_candidate(job_id, provider_id)

    def save_candidates(self, job_id: int, candidates: list[dict]):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id FROM match_candidate_statuses
                    WHERE code = 'ELIGIBLE' LIMIT 1
                    """
                )
                status_id = cursor.fetchone()["id"]

                for candidate in candidates:
                    cursor.execute(
                        """
                        INSERT INTO job_match_candidates
                            (
                                job_id, provider_id, status_id,
                                distance_km, within_service_area,
                                available_for_job, verified,
                                rating_average, experience_years,
                                match_score, generated_at
                            )
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE
                            status_id = VALUES(status_id),
                            distance_km = VALUES(distance_km),
                            within_service_area = VALUES(within_service_area),
                            available_for_job = VALUES(available_for_job),
                            verified = VALUES(verified),
                            rating_average = VALUES(rating_average),
                            experience_years = VALUES(experience_years),
                            match_score = VALUES(match_score),
                            generated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            job_id,
                            candidate["provider_id"],
                            status_id,
                            candidate["distance_km"],
                            int(candidate["within_service_area"]),
                            int(candidate["available_for_job"]),
                            int(candidate["verified"]),
                            candidate["rating_average"],
                            candidate["experience_years"],
                            candidate["match_score"],
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def list_saved(self, job_id: int, limit: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    jmc.provider_id,
                    pp.business_name,
                    pp.professional_title,
                    jmc.distance_km,
                    jmc.within_service_area,
                    jmc.available_for_job,
                    jmc.verified,
                    jmc.rating_average,
                    jmc.experience_years,
                    jmc.match_score
                FROM job_match_candidates jmc
                INNER JOIN provider_profiles pp
                    ON pp.id = jmc.provider_id
                INNER JOIN match_candidate_statuses mcs
                    ON mcs.id = jmc.status_id
                WHERE jmc.job_id = %s
                  AND mcs.code = 'ELIGIBLE'
                ORDER BY jmc.match_score DESC, jmc.distance_km ASC, jmc.provider_id ASC
                LIMIT %s
                """,
                (job_id, limit),
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows
