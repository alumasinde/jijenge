from app.database import db_connection


class LocationRepository:
    def set_provider_location(
        self,
        provider_id: int,
        latitude: float,
        longitude: float,
        address_line: str | None,
        accuracy_meters: float | None,
        is_primary: bool,
    ) -> dict:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                if is_primary:
                    cursor.execute(
                        """
                        UPDATE provider_locations
                        SET is_primary = 0
                        WHERE provider_id = %s
                          AND is_active = 1
                        """,
                        (provider_id,),
                    )

                cursor.execute(
                    """
                    INSERT INTO provider_locations
                        (
                            provider_id,
                            location_point,
                            address_line,
                            accuracy_meters,
                            is_primary
                        )
                    VALUES
                        (
                            %s,
                            ST_SRID(POINT(%s, %s), 4326),
                            %s,
                            %s,
                            %s
                        )
                    """,
                    (
                        provider_id,
                        longitude,
                        latitude,
                        address_line,
                        accuracy_meters,
                        int(is_primary),
                    ),
                )
                location_id = cursor.lastrowid
                connection.commit()

                cursor.execute(
                    """
                    SELECT
                        id,
                        ST_Y(location_point) AS latitude,
                        ST_X(location_point) AS longitude,
                        address_line,
                        accuracy_meters,
                        is_primary,
                        is_active
                    FROM provider_locations
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (location_id,),
                )
                row = cursor.fetchone()
                cursor.close()
                return row
            except Exception:
                connection.rollback()
                cursor.close()
                raise

    def list_provider_locations(self, provider_id: int) -> list[dict]:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    ST_Y(location_point) AS latitude,
                    ST_X(location_point) AS longitude,
                    address_line,
                    accuracy_meters,
                    is_primary,
                    is_active
                FROM provider_locations
                WHERE provider_id = %s
                  AND is_active = 1
                ORDER BY is_primary DESC, id DESC
                """,
                (provider_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def add_service_area(
        self,
        provider_id: int,
        latitude: float,
        longitude: float,
        radius_km: float,
        name: str | None,
    ) -> dict:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                INSERT INTO provider_service_areas
                    (provider_id, center_point, radius_km, name)
                VALUES
                    (
                        %s,
                        ST_SRID(POINT(%s, %s), 4326),
                        %s,
                        %s
                    )
                """,
                (provider_id, longitude, latitude, radius_km, name),
            )
            area_id = cursor.lastrowid
            connection.commit()

            cursor.execute(
                """
                SELECT
                    id,
                    ST_Y(center_point) AS latitude,
                    ST_X(center_point) AS longitude,
                    radius_km,
                    name,
                    is_active
                FROM provider_service_areas
                WHERE id = %s
                LIMIT 1
                """,
                (area_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def list_service_areas(self, provider_id: int) -> list[dict]:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    ST_Y(center_point) AS latitude,
                    ST_X(center_point) AS longitude,
                    radius_km,
                    name,
                    is_active
                FROM provider_service_areas
                WHERE provider_id = %s
                  AND is_active = 1
                ORDER BY id DESC
                """,
                (provider_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def create_job(
        self,
        customer_id: int,
        service_id: int,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        address_line: str | None,
        location_notes: str | None,
        budget_min,
        budget_max,
        preferred_start_at,
        preferred_end_at,
    ) -> int:
        with db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM job_statuses WHERE code = 'OPEN' AND is_active = 1 LIMIT 1"
                )
                status = cursor.fetchone()
                if not status:
                    raise RuntimeError("OPEN job status is missing")

                cursor.execute(
                    """
                    INSERT INTO jobs
                        (
                            customer_id, service_id, status_id, title,
                            description, budget_min, budget_max,
                            preferred_start_at, preferred_end_at
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        customer_id,
                        service_id,
                        status[0],
                        title,
                        description,
                        budget_min,
                        budget_max,
                        preferred_start_at,
                        preferred_end_at,
                    ),
                )
                job_id = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO job_locations
                        (
                            job_id, location_point,
                            address_line, location_notes
                        )
                    VALUES
                        (
                            %s,
                            ST_SRID(POINT(%s, %s), 4326),
                            %s,
                            %s
                        )
                    """,
                    (
                        job_id,
                        longitude,
                        latitude,
                        address_line,
                        location_notes,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO job_status_history
                        (job_id, status_id, changed_by_user_id, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        status[0],
                        customer_id,
                        "Job created",
                    ),
                )

                connection.commit()
                cursor.close()
                return int(job_id)
            except Exception:
                connection.rollback()
                cursor.close()
                raise

    def get_job(self, job_id: int, customer_id: int | None = None) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT
                    j.id,
                    j.customer_id,
                    j.service_id,
                    s.code AS service_code,
                    s.name AS service_name,
                    js.code AS status_code,
                    j.title,
                    j.description,
                    j.budget_min,
                    j.budget_max,
                    j.preferred_start_at,
                    j.preferred_end_at,
                    ST_Y(jl.location_point) AS latitude,
                    ST_X(jl.location_point) AS longitude,
                    jl.address_line,
                    jl.location_notes,
                    j.created_at,
                    j.updated_at
                FROM jobs j
                INNER JOIN services s ON s.id = j.service_id
                INNER JOIN job_statuses js ON js.id = j.status_id
                INNER JOIN job_locations jl ON jl.job_id = j.id
                WHERE j.id = %s
            """
            params = [job_id]
            if customer_id is not None:
                query += " AND j.customer_id = %s"
                params.append(customer_id)

            query += " LIMIT 1"

            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row

    def nearby_providers(
        self,
        service_id: int,
        latitude: float,
        longitude: float,
        radius_km: float,
        limit: int,
    ) -> list[dict]:
        # Distance is calculated on geographic POINT coordinates in meters.
        # Service-area matching checks whether the job point falls within
        # the provider's configured radius.
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pp.id AS provider_id,
                    pp.business_name,
                    pp.professional_title,
                    pp.is_verified,
                    ROUND(
                        ST_Distance_Sphere(
                            pl.location_point,
                            ST_SRID(POINT(%s, %s), 4326)
                        ) / 1000,
                        2
                    ) AS distance_km
                FROM provider_profiles pp
                INNER JOIN provider_services ps
                    ON ps.provider_id = pp.id
                   AND ps.service_id = %s
                   AND ps.is_active = 1
                INNER JOIN provider_statuses pst
                    ON pst.id = pp.provider_status_id
                   AND pst.code = 'ACTIVE'
                INNER JOIN provider_locations pl
                    ON pl.provider_id = pp.id
                   AND pl.is_active = 1
                   AND pl.is_primary = 1
                WHERE ST_Distance_Sphere(
                    pl.location_point,
                    ST_SRID(POINT(%s, %s), 4326)
                ) <= (%s * 1000)
                ORDER BY distance_km ASC, pp.is_verified DESC, pp.id ASC
                LIMIT %s
                """,
                (
                    longitude,
                    latitude,
                    service_id,
                    longitude,
                    latitude,
                    radius_km,
                    limit,
                ),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def nearby_providers_by_service_area(
        self,
        service_id: int,
        latitude: float,
        longitude: float,
        limit: int,
    ) -> list[dict]:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pp.id AS provider_id,
                    pp.business_name,
                    pp.professional_title,
                    pp.is_verified,
                    ROUND(
                        ST_Distance_Sphere(
                            psa.center_point,
                            ST_SRID(POINT(%s, %s), 4326)
                        ) / 1000,
                        2
                    ) AS center_distance_km,
                    psa.radius_km
                FROM provider_profiles pp
                INNER JOIN provider_services ps
                    ON ps.provider_id = pp.id
                   AND ps.service_id = %s
                   AND ps.is_active = 1
                INNER JOIN provider_statuses pst
                    ON pst.id = pp.provider_status_id
                   AND pst.code = 'ACTIVE'
                INNER JOIN provider_service_areas psa
                    ON psa.provider_id = pp.id
                   AND psa.is_active = 1
                WHERE ST_Distance_Sphere(
                    psa.center_point,
                    ST_SRID(POINT(%s, %s), 4326)
                ) <= (psa.radius_km * 1000)
                GROUP BY
                    pp.id,
                    pp.business_name,
                    pp.professional_title,
                    pp.is_verified,
                    psa.id,
                    psa.radius_km,
                    psa.center_point
                ORDER BY center_distance_km ASC, pp.is_verified DESC, pp.id ASC
                LIMIT %s
                """,
                (
                    longitude,
                    latitude,
                    service_id,
                    longitude,
                    latitude,
                    limit,
                ),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
