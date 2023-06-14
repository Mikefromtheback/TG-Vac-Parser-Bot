import config
import datetime
from psycopg_pool import AsyncConnectionPool


class DbInterface:
    nexus: AsyncConnectionPool
    new_user_time = datetime.datetime(2007, 1, 1, tzinfo=datetime.timezone.utc)

    async def initialize(self):  # hell
        try:
            self.nexus = AsyncConnectionPool(conninfo=config.dbinfo, kwargs={"autocommit": True})
        except Exception as info:
            print("[ERROR] Failed to initialize DbInterface:\n", info)
        else:
            print("[INFO] DbInterface initialized.")

    async def add_user(self, user_id, city, allow_remote, grade, allow_no_grade,
                       skills, additional_skills,
                       min_salary, allow_no_salary):
        try:
            async with self.nexus.connection() as connection_:
                async with connection_.cursor() as cursor_:
                    await cursor_.execute("""INSERT INTO 
                users(user_id, city, allow_remote, grade, allow_no_grade, skills, additional_skills, min_salary, allow_no_salary, last_updated) 
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                                          (user_id, city, allow_remote, list(grade), allow_no_grade, list(skills),
                                           list(additional_skills), min_salary, allow_no_salary, self.new_user_time))
                    return True
        except Exception as info:
            print("[ERROR] Failed to add user to database:\n", info)
            return False

    async def check_user(self, user_id):
        try:
            async with self.nexus.connection() as connection_:
                async with connection_.cursor() as cursor_:
                    await cursor_.execute("""SELECT * FROM users WHERE user_id = %s;""", (user_id,))
                    if await cursor_.fetchone() is None:
                        return 1
                    else:
                        return 0
        except Exception as info:
            print("[ERROR] Failed to check user existence:\n", info)
            return -1

    async def delete_user(self, user_id):
        try:
            async with self.nexus.connection() as connection_:
                async with connection_.cursor() as cursor_:
                    await cursor_.execute("""DELETE FROM users WHERE user_id = %s;""", (user_id,))
                    return True
        except Exception as info:
            print("[ERROR] Failed to erase user:\n", info)
            return False

    async def update_user_time(self, user_id, new_value):
        try:
            async with self.nexus.connection() as connection_:
                async with connection_.cursor() as cursor_:
                    await cursor_.execute("""UPDATE users SET last_updated = %s WHERE user_id = %s""",
                                          (new_value, user_id))
        except Exception as info:
            print("[ERROR] Failed to update time for user:\n", info)

    async def get_vacancies(self, user_id: int):
        try:
            async with self.nexus.connection() as connection_:
                async with connection_.cursor() as cursor_:
                    await cursor_.execute("""SELECT * FROM users WHERE user_id = %s;""", (user_id,))
                    user_data = await cursor_.fetchone()
                    await cursor_.execute("""SELECT company_name, vacancy_name, vacancy_url, publication_date FROM new_vacancies
                    WHERE (city && %s::varchar[] OR (is_online = TRUE AND %s = TRUE))
                    AND (grade = ANY(%s::varchar[]) OR (grade is NULL AND %s = TRUE))
                    AND (specialization = ANY(%s::varchar[]))
                    AND (%s::varchar[] && skills OR (%s = '{}')) 
                    AND (%s <= lower(salary) OR (salary is NULL AND %s = TRUE))
                    AND (%s < publication_date)
                    ORDER BY publication_date ASC
                    LIMIT 10;
                    """,
                                          (user_data[1], user_data[2], user_data[3], user_data[4], user_data[5],
                                           user_data[6], user_data[6], user_data[7], user_data[8], user_data[9]))
                    return await cursor_.fetchall()

        except Exception as exc:
            print("[INFO] Error encountered while getting vacancies:\n", exc)
            return None
