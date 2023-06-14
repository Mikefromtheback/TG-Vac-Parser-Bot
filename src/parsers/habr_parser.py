import asyncio
import re
import aiohttp
from tqdm import tqdm
from tqdm import trange
from bs4 import BeautifulSoup
from currency_exchange import CurrencyExchange
from db import DataBase
from spec_to_spec import spec_to_spec


START_URl = 'https://career.habr.com'
MID_URl = '/vacancies?page='
END_URL = '&type=all'

db = DataBase()


def formatting(text):
    text = re.sub(r'\n+', r'\n', text)
    text = text.replace('\t', ' ')
    text = text.replace('​', ' ')
    text = text.replace(' ', ' ')
    text = re.sub(r' +', r' ', text)
    text = text.replace('\n ', '\n')
    while len(text) > 1 and text[0] == ' ':
        text = text[1:]
    return text


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    print(f'[WARNING] habr connection error, response code is {resp.status}, url is {url}')
                    return None
        except aiohttp.ClientConnectorError as e:
            print('[WARNING] connection with habr error', str(e))


grades = ['стажёр (intern)', 'младший (junior)', 'средний (middle)', 'старший (senior)', 'ведущий (lead)']

good_specialization = ['Инженер по автоматизации тестирования', 'Девопс инженер', 'Системный аналитик',
                       'Разработчик мобильных приложений', 'Архитектор программного обеспечения',
                       'Администратор баз данных', 'Аналитик по данным', 'Бэкенд разработчик', 'Программист 1С',
                       'Фронтенд разработчик', 'Разработчик баз данных', 'Администратор серверов',
                       'Инженер по производительности', 'Инженер по безопасности', 'Бизнес-аналитик',
                       'Администратор защиты', 'Инженер по данным', 'Фулстек разработчик', 'Веб-разработчик',
                       'Менеджер технической поддержки', 'Инженер встраиваемых систем', 'Архитектор баз данных',
                       'Инженер технической поддержки', 'Десктоп разработчик', 'Системный администратор',
                       'Продуктовый аналитик', 'Инженер по обеспечению качества', 'Инженер по ручному тестированию',
                       'Учёный по данным', 'Системный инженер', 'Технический писатель', 'Разработчик игр',
                       'Бэкенд разработчик ruby', 'Администратор сетей', 'Технический директор', 'Пентестер']

stoplist_skills = ['ведение переговоров', 'scrum', 'управление проектами', 'управление бизнес-процессами']

languages = ['c++', 'python', 'golang', 'java', 'php', 'c#', 'node.js', 'scala', 'ruby']


async def processing_salary(salary, index_from, index_to):  # перевод в доллары
    salary_from = salary[3:index_to - 1].replace(' ', '')
    salary_to = salary[index_to + 3:-2].replace(' ', '')
    if index_from == -1 or index_to == -1:
        return None
    if salary:
        if salary[-1] != '$' and salary[-1] != '€':
            # RUB
            salary_from = await CurrencyExchange.convert(int(salary_from), 'RUB')
            salary_to = await CurrencyExchange.convert(int(salary_to), 'RUB')
        elif salary[-1] == '€':
            # EUR
            salary_from = await CurrencyExchange.convert(int(salary_from), 'EUR')
            salary_to = await CurrencyExchange.convert(int(salary_to), 'EUR')
        else:
            # USD
            salary_from = int(salary_from)
            salary_to = int(salary_to)
        return f'[{salary_from},{salary_to}]'
    return None


def processing_specialization(specialization):  # то что мы порешили с андреем сегодня
    if specialization == 'Системный инженер':
        specialization = 'Девопс инженер'
    elif specialization == 'Веб-разработчик':
        specialization = 'Фулстек разработчик'
    elif specialization == 'Администратор серверов' or specialization == 'Администратор сетей':
        specialization = 'Системный администратор'
    elif specialization == 'Администратор баз данных' or specialization == 'Архитектор баз данных':
        specialization = 'DA/DBA'
    elif specialization == 'Администратор защиты' or specialization == 'Пентестер' or specialization == 'Инженер по безопасности':
        specialization = 'Специалист по ИБ'
    elif specialization == 'Инженер по ручному тестированию' or specialization == 'Инженер по автоматизации тестирования' or specialization == 'Инженер по обеспечению качества' or specialization == 'Инженер по производительности':
        specialization = 'QA тестировщик'
    elif specialization == 'Инженер технической поддержки' or specialization == 'Менеджер технической поддержки':
        specialization = 'Специалист по технической поддержке'
    return specialization


def processing_name(name):  # умные хэры могут спокойно написать C русской буквой, реплейсим все такие случаи
    index = re.search(r'[^a-zа-я1]' + 'с' + r'[^a-zа-я]', (' ' + name.lower() + ' '))
    while index:
        index = index.span()[0]
        name = name[:index] + 'C' + name[index + 1:]
        index = re.search(r'[^a-zа-я1]' + 'с' + r'[^a-zа-я]', (' ' + name.lower() + ' '))
    return name


def get_description(page):
    soup_second = BeautifulSoup(page, features='lxml')  # здесь начинается работа по доставанию описания
    all_text_blocks = soup_second.find('div', class_='vacancy-description__text').find_all(['p', 'h3', 'ul', 'ol'])
    for text_block in all_text_blocks:
        if (text_block.name == 'p' or text_block.name == 'h3') and text_block.string:
            text_block.string = text_block.string.replace('\n', '')
            continue
        for li in text_block.find_all('li'):
            if li.string:
                li.string = li.string.replace('\n', '')
    for br in soup_second.find_all('br'):
        br.replace_with('\n')
    description = ''
    for text_block in all_text_blocks:
        if text_block.name == 'p' or text_block.name == 'h3':
            if text_block.get_text() == '':
                continue
            description += ('\n' + formatting(text_block.get_text()))
            continue
        if text_block.parent.name == 'li':
            continue
        for li in text_block.find_all('li'):
            if li.parent.parent.name == 'li':
                continue
            include_list = None
            for child in li.children:
                if child.name == 'ul' or child.name == 'ol':
                    include_list = child
                    break
            if include_list:
                description += ('\n' + li.get_text().replace(include_list.get_text(), ''))
                for include_li in include_list.find_all('li'):
                    if include_li.get_text() == '':
                        continue
                    description += ('\n' + formatting(include_li.get_text()))
                continue
            if li.get_text() == '':
                continue
            description += ('\n' + formatting(li.get_text()))
    description = re.sub(r'\n+', r'\n', description)
    description = description.replace('\n \n', '\n')
    description = description[1:]
    while description[-1] == '\n' or description[-1] == ' ':
        description = description[:-1]
    return description


def processing_backend(name, skills, description):
    specialization = 'Бэкенд разработчик'
    counter = -1
    is_found_in_name = False
    is_one_in_skills = True
    for i in range(len(languages)):  # сначала ищем язык в скилах, при этом смотрим чтобы он был единственный
        if languages[i] in skills:
            if counter != -1:
                is_one_in_skills = False
                break
            counter = i
    if counter == -1:
        is_one_in_skills = False
    if is_one_in_skills:  # нашли
        specialization = specialization + ' ' + languages[counter]
    else:  # не нашли, ищем в имени
        for i in range(len(languages)):
            if languages[i] == 'golang':  # т.к. где то пишут go вместо golang
                if re.search(r'[^a-zа-я]' + 'go' + r'[^a-zа-я]', ' ' + name.lower() + ' '):
                    specialization += ' golang'
                    is_found_in_name = True
                    break
            override_error = languages[i]
            if languages[i] == 'c++':
                override_error = 'c\+\+'  # делаем так т.к. в регулярках плюс это специальный символ
            if re.search(r'[^a-zа-я]' + override_error + r'[^a-zа-я]', ' ' + name.lower() + ' '):
                specialization += (' ' + languages[i])
                is_found_in_name = True  # нашли
                break

        if not is_found_in_name:  # не нашли, считаем количество вхождений в описание каждого языка, берем наиболее частый
            maximum = 0
            counter = -1
            for i in range(len(languages)):
                override_error = languages[i]
                if languages[i] == 'c++':
                    override_error = 'c\+\+'
                include_number = len(re.findall(r'[^a-zа-я]' + override_error + r'[^a-zа-я+#]', description.lower()))
                if languages[i] == 'golang':
                    include_number += len(re.findall(r'[^a-zа-я]' + 'go' + r'[^a-zа-я]', description.lower()))
                if maximum < include_number:
                    maximum = include_number
                    counter = i
            if counter != -1:
                specialization += (' ' + languages[counter])
            elif ('.net' in skills) or ('.net core' in skills):
                specialization += (' ' + 'c#')
            else:
                return None
    return specialization


async def parse_vacancy(vacancy):
    company = vacancy.find('a', class_='link-comp link-comp--appearance-dark').get_text()
    name = vacancy.find('a', class_='vacancy-card__title-link').get_text()
    name = processing_name(name)
    link = vacancy.find('a', class_='vacancy-card__title-link').get('href')
    vacancy_url = START_URl + link
    page = await get_html(vacancy_url)
    if page is None:
        return
    salary = vacancy.find('div', class_='basic-salary').get_text()
    index_from = salary.find('от')
    index_to = salary.find('до')
    salary = await processing_salary(salary, index_from, index_to)
    public_datetime = vacancy.find('time', class_='basic-date').get('datetime')
    geo = vacancy.find('div', class_='vacancy-card__meta')
    cities = geo.find_all('a', class_='link-comp link-comp--appearance-dark')
    geo = geo.find_all('span', class_='preserve-line')
    is_online = False
    for i in range(len(geo)):
        geo[i] = geo[i].get_text()
        if geo[i] == 'Можно удаленно':
            is_online = True
    cities = geo[0:len(cities)]
    if not cities:
        cities = None

    skills = vacancy.find('div', class_='vacancy-card__skills')
    skills = skills.find_all('a', class_='link-comp link-comp--appearance-dark')
    grade = None
    is_exit = False
    for i in range(len(skills)):  # здесь обрабатываем скилы, вычленяем грейд если он есть
        skills[i] = skills[i].get_text()
        if i > 0:
            skills[i] = skills[i].lower()
        if skills[i] in stoplist_skills:
            is_exit = True
            break
        if i == 1 and (skills[i] in grades):
            grade = skills[i][skills[i].find('(') + 1:skills[i].find(')')]
    specialization = skills.pop(0)
    if grade:
        skills.pop(0)
    if (specialization not in good_specialization) or is_exit:
        return

    specialization = processing_specialization(specialization)
    description = get_description(page)

    if specialization == 'Бэкенд разработчик':  # здесь начинаем разделение бэкэнда на части
        specialization = processing_backend(name, skills, description)
        if specialization is None:
            return
    specialization = spec_to_spec[specialization]
    query = """INSERT INTO temp_vacancies(company_name, vacancy_name, vacancy_url, publication_date, salary, grade, city, is_online, skills, specialization, vacancy_description) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    record_data = (
        company, name, vacancy_url, public_datetime, salary, grade, cities, is_online, skills, specialization,
        description,)
    await db.write(query, record_data)


async def parse_page(html, page = 0):  # парсим страницу с вакансиями
    if html is None:
        return 0
    soup = BeautifulSoup(html, features='lxml').find('div', class_='page-container')
    vacancies = soup.find_all('div', class_='section-box')
    if soup.find('div', class_='no-content'):  # если пустая страница то кикаемся
        return -1

    tasks = []
    for vacancy in tqdm(vacancies[1:-2], desc=f'habr vacancies on {page} page'):  # начинаем идти по самим вакансиям
        task = asyncio.create_task(parse_vacancy(vacancy))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def parse_habr():
    for page in trange(1, 200, desc='habr pages'):
        html = await get_html(START_URl + MID_URl + str(page) + END_URL)
        code = await parse_page(html, page)
        if code == -1:
            break


async def get_vacancies():
    open_db_task = asyncio.create_task(db.open())
    parse_task = asyncio.create_task(parse_habr())

    await open_db_task
    await parse_task


def fetch_habr_vacancies():
    asyncio.run(get_vacancies())
