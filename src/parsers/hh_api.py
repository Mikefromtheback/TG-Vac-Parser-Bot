import asyncio
import aiohttp
from sklearn.feature_extraction.text import TfidfVectorizer
from currency_exchange import CurrencyExchange
from db import DataBase
from processing_description import processing_description
from preparation_data import id_to_category
from spec_to_spec import spec_to_spec
import pickle
from tqdm import tqdm
from tqdm import trange

URL = 'https://api.hh.ru/vacancies'

db = DataBase()
professional_role = [
    {
        "id": "160",
        "name": "DevOps-инженер",
    },
    {
        "id": "10",
        "name": "Аналитик",
    },
    {
        "id": "150",
        "name": "Бизнес-аналитик",
    },
    {
        "id": "165",
        "name": "Дата-сайентист",
    },
    {
        "id": "96",
        "name": "Программист, разработчик",
    },
    {
        "id": "164",
        "name": "Продуктовый аналитик",
    },
    {
        "id": "112",
        "name": "Сетевой инженер",
    },
    {
        "id": "113",
        "name": "Системный администратор",
    },
    {
        "id": "148",
        "name": "Системный аналитик",
    },
    {
        "id": "114",
        "name": "Системный инженер",
    },
    {
        "id": "116",
        "name": "Специалист по информационной безопасности",
    },
    {
        "id": "124",
        "name": "Тестировщик",
    },
    {
        "id": "125",
        "name": "Технический директор (CTO)",
    },
]


async def async_req_get(url, params):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f'[WARNING] hh connection error, response code is {resp.status}, url is {url}')
                    return None
        except aiohttp.ClientConnectorError as e:
            print('[WARNING] connection with hh error', str(e))


async def send_vacancy_to_db(vacancy):
    query = """INSERT INTO temp_vacancies(company_name, vacancy_name, vacancy_url, publication_date, salary, grade, city, is_online, skills, specialization, vacancy_description) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    record_data = (
        vacancy['company_name'], vacancy['vacancy_name'], vacancy['vacancy_url'], vacancy['publication_date'],
        vacancy['salary'], vacancy['grade'], vacancy['city'], vacancy['is_online'], vacancy['skills'],
        vacancy['specialization'], vacancy['vacancy_description'],)
    await db.write(query, record_data)


def get_specialization(vacancy_description):
    new_vacancy_description = processing_description(vacancy_description)
    file_tfidf = 'saved_tfidf.pkl'
    tmp_features = pickle.load(open(file_tfidf, 'rb'))
    file_model = 'saved_model.sav'
    model = pickle.load(open(file_model, 'rb'))
    vect = TfidfVectorizer(sublinear_tf=True, norm='l2', ngram_range=(1, 2), vocabulary=tmp_features.vocabulary_)
    tfidf_of_vacancy = vect.fit_transform([new_vacancy_description])
    return spec_to_spec[id_to_category[model.predict(tfidf_of_vacancy)[0]]]


async def fetch_vacancy(id):
    vacancy_json = await async_req_get(URL + '/' + str(id), None)
    if vacancy_json is None:
        return

    vacancy_data = {'company_name': vacancy_json['employer']['name'], 'vacancy_name': vacancy_json['name'],
                    'vacancy_url': vacancy_json['alternate_url'], 'publication_date': vacancy_json['created_at'],
                    'city': [vacancy_json['area']['name']], 'vacancy_description': vacancy_json['description'],
                    'skills': []}

    for skills in vacancy_json['key_skills']:
        vacancy_data['skills'].append(skills['name'])

    # add different currency
    if vacancy_json['salary'] is not None:
        currency = vacancy_json['salary']['currency']
        if currency == 'RUR':
            currency = 'RUB'
        if currency == 'BYR':
            currency = 'BYN'
        salary_from = vacancy_json['salary']['from']
        salary_to = vacancy_json['salary']['to']
        if salary_from is not None and salary_to is not None:
            if currency != 'USD':
                salary_from = await CurrencyExchange.convert(salary_from, currency)
                salary_to = await CurrencyExchange.convert(salary_to, currency)
            vacancy_data['salary'] = f'[{salary_from},{salary_to}]'
        else:
            vacancy_data['salary'] = None
    else:
        vacancy_data['salary'] = None
    # add grade
    match vacancy_json['experience']['id']:
        case 'noExperience':
            vacancy_data['grade'] = 'Intern'
        case 'between1And3':
            vacancy_data['grade'] = 'Junior'
        case 'between3And6':
            vacancy_data['grade'] = 'Middle'
        case 'moreThan6':
            vacancy_data['grade'] = 'Senior'

    vacancy_data['is_online'] = False
    if vacancy_json['schedule']['id'] == 'remote':
        vacancy_data['is_online'] = True
    vacancy_data['specialization'] = get_specialization(vacancy_data['vacancy_description'])
    await send_vacancy_to_db(vacancy_data)


async def fetch_list_of_vacancies(professional_role_id, page=0):
    params = {
        'page': page,
        'per_page': 100,
        'professional_role': professional_role_id,
    }

    response_json = await async_req_get(URL, params)
    if response_json is None:
        return 0
    pages = response_json['pages']
    for vacancy in tqdm(response_json['items'], desc=f'hh vacancies on {page + 1} page'):
        await fetch_vacancy(vacancy['id'])
    return pages


async def get_hh_vacancies():
    for professional_role_data in tqdm(professional_role, desc='hh professional roles'):
        pages = await fetch_list_of_vacancies(professional_role_data['id'])
        for page in trange(1, pages, desc='hh pages'):
            await fetch_list_of_vacancies(professional_role_data['id'], page)


async def create_tasks():
    open_db_task = asyncio.create_task(db.open())
    get_vacancies_task = asyncio.create_task(get_hh_vacancies())

    await open_db_task
    await get_vacancies_task


def fetch_hh_vacancies():
    asyncio.run(create_tasks())
