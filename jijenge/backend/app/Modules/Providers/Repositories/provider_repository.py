from app.database import db_connection


class ProviderRepository:
    def get_status_id(self, code: str) -> int:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM provider_statuses WHERE code = %s AND is_active = 1 LIMIT 1",
                (code,),
            )
            row = cursor.fetchone()
            cursor.close()
            if not row:
                raise RuntimeError(f"Provider status {code} is missing")
            return int(row[0])

    def get_profile_by_user(self, user_id: int) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pp.id,
                    pp.user_id,
                    ps.code AS status_code,
                    pp.business_name,
                    pp.professional_title,
                    pp.bio,
                    pp.years_experience,
                    pp.is_verified
                FROM provider_profiles pp
                INNER JOIN provider_statuses ps ON ps.id = pp.provider_status_id
                WHERE pp.user_id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def create_profile(self, user_id, business_name, professional_title, bio, years_experience):
        with db_connection() as connection:
            cursor = connection.cursor()
            status_id = self.get_status_id("PENDING")
            cursor.execute(
                """
                INSERT INTO provider_profiles
                    (user_id, provider_status_id, business_name,
                     professional_title, bio, years_experience)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, status_id, business_name, professional_title, bio, years_experience),
            )
            connection.commit()
            cursor.close()
        return self.get_profile_by_user(user_id)

    def update_profile(self, user_id, business_name, professional_title, bio, years_experience):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE provider_profiles
                SET business_name = %s,
                    professional_title = %s,
                    bio = %s,
                    years_experience = %s
                WHERE user_id = %s
                """,
                (business_name, professional_title, bio, years_experience, user_id),
            )
            connection.commit()
            cursor.close()
        return self.get_profile_by_user(user_id)

    def service_exists(self, service_id: int) -> bool:
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM services s
                INNER JOIN service_categories c ON c.id = s.category_id
                WHERE s.id = %s AND s.is_active = 1 AND c.is_active = 1
                LIMIT 1
                """,
                (service_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row is not None

    def add_service(self, provider_id, service_id, years_experience, minimum_price, maximum_price):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO provider_services
                    (provider_id, service_id, years_experience,
                     minimum_price, maximum_price)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    years_experience = VALUES(years_experience),
                    minimum_price = VALUES(minimum_price),
                    maximum_price = VALUES(maximum_price),
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (provider_id, service_id, years_experience, minimum_price, maximum_price),
            )
            connection.commit()
            cursor.close()

    def list_services(self, provider_id: int):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    ps.service_id,
                    s.code AS service_code,
                    s.name AS service_name,
                    ps.years_experience,
                    ps.minimum_price,
                    ps.maximum_price,
                    ps.is_active
                FROM provider_services ps
                INNER JOIN services s ON s.id = ps.service_id
                WHERE ps.provider_id = %s
                ORDER BY s.name
                """,
                (provider_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def discover(
        self,
        service_id: int | None,
        latitude: float,
        longitude: float,
        radius_km: float,
        limit: int,
        verified_only: bool = False,
    ):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            service_filter = ""
            params = [longitude, latitude]

            if service_id is not None:
                service_filter = """
                    INNER JOIN provider_services psv
                        ON psv.provider_id = pp.id
                       AND psv.service_id = %s
                       AND psv.is_active = 1
                """
                params.append(service_id)

            verified_filter = ""
            if verified_only:
                verified_filter = " AND pp.is_verified = 1 "

            params.extend([longitude, latitude, radius_km, limit])

            sql = """
                SELECT
                    pp.id AS provider_id,
                    pp.business_name,
                    pp.professional_title,
                    pp.bio,
                    pp.years_experience,
                    pp.is_verified,
                    ROUND(
                        ST_Distance_Sphere(
                            pl.location_point,
                            ST_SRID(POINT(%s, %s), 4326)
                        ) / 1000,
                        2
                    ) AS distance_km,
                    GROUP_CONCAT(DISTINCT s.name ORDER BY s.name SEPARATOR ', ') AS service_names
                FROM provider_profiles pp
                INNER JOIN provider_statuses pst
                    ON pst.id = pp.provider_status_id
                   AND pst.code = 'ACTIVE'
                INNER JOIN provider_locations pl
                    ON pl.provider_id = pp.id
                   AND pl.is_primary = 1
                   AND pl.is_active = 1
                {service_filter}
                LEFT JOIN provider_services ps
                    ON ps.provider_id = pp.id
                   AND ps.is_active = 1
                LEFT JOIN services s
                    ON s.id = ps.service_id
                   AND s.is_active = 1
                WHERE ST_Distance_Sphere(
                    pl.location_point,
                    ST_SRID(POINT(%s, %s), 4326)
                ) <= (%s * 1000)
                {verified_filter}
                GROUP BY
                    pp.id,
                    pp.business_name,
                    pp.professional_title,
                    pp.bio,
                    pp.years_experience,
                    pp.is_verified,
                    pl.location_point
                ORDER BY distance_km ASC, pp.is_verified DESC, pp.id ASC
                LIMIT %s
                """.format(
                    service_filter=service_filter,
                    verified_filter=verified_filter,
                )
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
