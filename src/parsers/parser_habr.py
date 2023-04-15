import sys
import datetime
import requests
from bs4 import BeautifulSoup

import config
import psycopg2
from psycopg2 import Error

START_URl = "https://career.habr.com"
MID_URl = "/vacancies?page="
END_URL = "&type=all"


# def formatting(text):
#     text.replace('\n\n\n', '\n')
#     text.replace('\t', ' ')
#     text.replace('  ', ' ')
#     text.replace('  ', ' ')
#     lol = 0
#     kek = 0
#     troll = 0
#     while lol == 0:
#         for i in range(troll, len(text)):
#             if text[i] != '\n':
#                 kek += 1
#             else:
#                 if kek < 5:
#                     text = text[:i] + text[i + 1:]
#                     kek = 0
#                     troll = i - 1
#                     break
#                 kek = 0
#             if i == len(text) - 1:
#                 lol = 1
#     return text


def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print("Error")
        quit()


def currency_usd():
    data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    return data['Valute']['USD']['Value']


def currency_eur():
    data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    return data['Valute']['EUR']['Value']


course_usd = currency_usd()
course_eur = currency_eur()
grades = ["Младший (Junior)", "Средний (Middle)", "Старший (Senior)", "Ведущий (Lead)"]


def to_int(string, course):
    if string:
        string = round(int(string) / course)
    return string


def processing_salary(salary, index_from, index_to):
    salary_from = salary[3:index_to - 1].replace(" ", "")
    salary_to = salary[index_to + 3:-2].replace(" ", "")
    if index_from == -1:
        salary_from = None
    if index_to == -1:
        salary_to = None
    if salary:
        if salary[-1] != '$' and salary[-1] != '€':
            salary_from = to_int(salary_from, course_usd)
            salary_to = to_int(salary_to, course_usd)
        elif salary[-1] == '€':
            salary_from = to_int(salary_from, course_usd/course_eur)
            salary_to = to_int(salary_to, course_usd/course_eur)
        else:
            salary_from = to_int(salary_from, 1)
            salary_to = to_int(salary_to, 1)
    return salary_from, salary_to

def parse(html):
    soup = BeautifulSoup(html, features="lxml").find('div', class_='page-container')
    vacancies = soup.find_all('div', class_='section-box')
    if soup.find('div', class_='no-content'):
        sys.exit()
    for vacancy in vacancies[1:-2]:
        company = vacancy.find('a', class_='link-comp link-comp--appearance-dark').get_text()
        name = vacancy.find('a', class_='vacancy-card__title-link').get_text()
        link = vacancy.find('a', class_='vacancy-card__title-link').get('href')
        salary = vacancy.find('div', class_='basic-salary').get_text()
        index_from = salary.find("от")
        index_to = salary.find("до")
        salary_from, salary_to = processing_salary(salary, index_from, index_to)
        date_time = vacancy.find('time', class_='basic-date').get('datetime')[:-6]
        date, time = date_time.split("T")
        date = date.split("-")
        time = time.split(":")
        date_time = datetime.datetime(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]),
                                      int(time[2]))
        skills = vacancy.find('div', class_='vacancy-card__skills')
        skills = skills.find_all('a', class_='link-comp link-comp--appearance-dark')
        geo = vacancy.find('div', class_='vacancy-card__meta')
        cities = geo.find_all('a', class_='link-comp link-comp--appearance-dark')
        geo = geo.find_all('span', class_='preserve-line')
        online = False
        for i in range(len(geo)):
            geo[i] = geo[i].get_text()
            if geo[i] == "Можно удаленно":
                online = True
        cities = geo[0:len(cities)]
        if not cities:
            cities = None
        grade = None
        for i in range(len(skills)):
            skills[i] = skills[i].get_text()
            if i == 1 and (skills[i] in grades):
                grade = skills[i][skills[i].find("(") + 1:skills[i].find(")")]
        if grade:
            skills.pop(1)
        # soup_second = BeautifulSoup(get_html(START_URl + link), features="lxml")
        # description = soup_second.find('div', class_='vacancy-description__text').get_text(separator="\n")
        # description = formatting(description)
        insert_to_database(company, name, salary_from, salary_to, grade, skills, online, cities,
              START_URl + link, date_time)

def insert_to_database(company, name, salary_from, salary_to, grade, skills, online, cities, vacancy_url, public_time):
    try:
        # Подключение к существующей базе данных
        connection = psycopg2.connect(
            host=config.dbhost,
            database=config.dbname,
            user=config.dbuser,
            password=config.dbpassword,
            port=config.dbport
        )

        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        # Выполнение SQL-запроса
        salary_string = None
        if salary_from is not None and salary_to is not None:
            salary_string = "[" + str(salary_from) + "," + str(salary_to) + "]"
        record_data = (company, name, vacancy_url, public_time, salary_string, grade, cities, online, skills, )
        cursor.execute("""INSERT INTO new_vacancies(company_name, vacancy_name, vacancy_url, publication_date, salary, grade, city, is_online, skills) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)""", record_data)
        connection.commit()
        print("Данные отправились")

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL, ERROR: ", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


def main():
    for i in range(1, 1000):
        parse(get_html(START_URl + MID_URl + str(i) + END_URL))


if __name__ == '__main__':
    main()
