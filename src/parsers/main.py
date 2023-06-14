import multiprocessing
from habr_parser import fetch_habr_vacancies
from hh_api import fetch_hh_vacancies
from db import DataBase
import schedule
import time


def start_fetch_vacancies():
    process_fetch_vacancies_from_habr = multiprocessing.Process(target=fetch_habr_vacancies)
    process_fetch_vacancies_from_hh = multiprocessing.Process(target=fetch_hh_vacancies)

    process_fetch_vacancies_from_habr.start()
    process_fetch_vacancies_from_hh.start()

    process_fetch_vacancies_from_habr.join()
    process_fetch_vacancies_from_hh.join()


def main():
    db = DataBase()
    try:
        db.create_temp_table()
        start_fetch_vacancies()
    except Exception:
        print(f'[WARNING] {Exception}')
    finally:
        db.rename_table()


if __name__ == '__main__':
    schedule.every().day.at("00:00").do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
