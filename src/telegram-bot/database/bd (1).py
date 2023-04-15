import config
import psycopg2
from datetime import datetime

new_user_time = datetime(2007, 1, 1)


class DbInterface:
    def __init__(self, connection):
        self.conn = connection

    def add_user(self, id, city, isonl, grade, skils, min_salary):
        with conn.cursor() as curs:
            try:
                curs.execute("""INSERT INTO 
                users(user_id, city, remote_allowed, grade, skills, min_salary, last_updated) 
                VALUES(%s, %s, %s, %s, %s, %s, %s);""",
                             (id, city, isonl, grade, skils, min_salary, new_user_time))
            except Exception as exc:
                print("[INFO] Error encountered.", exc)

    def check_user(self, id):
        with conn.cursor() as curs:
            curs.execute("SELECT * FROM users WHERE user_id = %s;", (id,))
            return not curs.fetchone() is None

    def delete_user(self, id):
        with conn.cursor() as curs:
            return curs.execute("DELETE FROM users WHERE user_id = %s;", (id,))

    def update_user_time(self, id, new_value):
        with conn.cursor() as curs:
            return curs.execute("UPDATE users SET last_updated = %s WHERE user_id = %s", (new_value, id))

    def get_users(self):
        with conn.cursor() as curs:
            curs.execute("SELECT * FROM users;")
            return curs.fetchall()

    def get_user_data(self, id):
        with conn.cursor() as curs:
            curs.execute("SELECT * FROM users WHERE user_id = %s;", (id,))
            return curs.fetchone()

    def get_vacancies(self, user_data: tuple[int, str, bool, str, tuple[str], int, datetime]):
        with conn.cursor() as curs:
            try:
                user_id, city, remote_allowed, grade, skills, min_salary, last_updated = user_data
                curs.execute("""SELECT * FROM new_vacancies 
                WHERE (city && ARRAY[%s::varchar] OR (is_online = TRUE AND %s = TRUE))
                AND %s = grade 
                AND skills && %s::varchar[]
                AND (%s <= lower(salary) OR %s = 0)
                AND %s < publication_date;""",
                             (city, remote_allowed, grade, skills, min_salary, min_salary, last_updated))
                return curs.fetchall()
            except Exception as exc:
                print("[INFO] Error encountered while getting vacancies.", exc)


try:
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        user=config.dbuser,
        password=config.dbpassword,
        port=config.dbport
    )
    print("[INFO] Connection established.")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM new_vacancies WHERE id = 22;")
    db = DbInterface(conn)
    pass
except Exception as exc:
    print("[INFO] Error encountered.", exc)
finally:
    print("[INFO] OK")
