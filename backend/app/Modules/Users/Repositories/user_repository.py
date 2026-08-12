from app.database import db_connection


class UserRepository:
    def get_profile(self, user_id: int) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, user_id, first_name, last_name, bio, profile_photo_url
                FROM user_profiles
                WHERE user_id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def update_profile(
        self,
        user_id: int,
        first_name: str,
        last_name: str,
        bio: str | None,
        profile_photo_url: str | None,
    ) -> dict | None:
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                UPDATE user_profiles
                SET first_name = %s,
                    last_name = %s,
                    bio = %s,
                    profile_photo_url = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, bio, profile_photo_url, user_id),
            )
            connection.commit()
            cursor.close()
        return self.get_profile(user_id)
