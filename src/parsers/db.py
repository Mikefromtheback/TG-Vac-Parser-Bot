import config
import psycopg_pool
import psycopg
from psycopg import Error


class DataBase:

    def __init__(self):
        self.conninfo = f'host=ep-twilight-butterfly-537431.us-east-2.aws.neon.tech port={5432} dbname=botdb user=root password=z0iqhd5UCsnv'
        self.__pool = psycopg_pool.AsyncConnectionPool(conninfo=config.conninfo, open=False)

    def clear_db(self):
        try:
            with psycopg.connect(config.conninfo) as conn:
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM temp_vacancies;')
                    conn.commit()
        except psycopg.OperationalError as e:
            print(f'[WARNING] database operation error, {e.sqlstate}, {e.args}')

    def create_temp_table(self):
        try:
            with psycopg.connect(self.conninfo) as conn:
                with conn.cursor() as cur:
                    cur.execute("""CREATE TABLE temp_vacancies(
                                    id BIGSERIAL PRIMARY KEY,
                                    company_name VARCHAR(150) NOT NULL,
                                    vacancy_name VARCHAR(150) NOT NULL,
                                    vacancy_url VARCHAR(150) NOT NULL,
                                    publication_date TIMESTAMPTZ NOT NULL,
                                    salary INT4RANGE,
                                    grade VARCHAR(6),
                                    city VARCHAR(150)[],
                                    is_online BOOLEAN NOT NULL,
                                    skills VARCHAR(150)[],
                                    specialization VARCHAR(150),
                                    vacancy_description TEXT
                                    );""")
                    conn.commit()
        except psycopg.OperationalError as e:
            print(f'[WARNING] database operation error, {e.sqlstate}, {e.args}')

    def rename_table(self):
        try:
            with psycopg.connect(self.conninfo) as conn:
                with conn.cursor() as cur:
                    cur.execute('DROP TABLE vacancies;')
                    cur.execute('ALTER TABLE temp_vacancies RENAME TO vacancies;')
                    conn.commit()
        except psycopg.OperationalError as e:
            print(f'[WARNING] database operation error, {e.sqlstate}, {e.args}')

    async def open(self):
        try:
            await self.__pool.open()
            print('[INFO] database pool connection open')
        except (Exception, Error) as e:
            print(f'[WARNING] database connection not open, {e}')

    async def select_fetchall(self, query, args):
        try:
            async with self.__pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    results = await cursor.fetchall()
                    return results
        except psycopg.OperationalError as e:
            print(f'[WARNING] database operation error, {e.sqlstate}, {e.args}')

    async def write(self, query, args):
        try:
            async with self.__pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    if 'RETURNING' in query:
                        results = await cursor.fetchone()
                        return results
                    else:
                        return
        except psycopg.OperationalError as e:
            print(f'[WARNING] database operation error, {e.sqlstate}, {e.args}')
