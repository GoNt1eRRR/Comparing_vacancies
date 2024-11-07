import os
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_hh_vacancies(language):
    url = 'https://api.hh.ru/vacancies'
    vacancies = []
    page = 0
    total_pages = 1
    vacancies_found = 0
    moscow_area_id = 1
    search_period = 30
    per_page = 100
    params = {
        'text': language,
        'area': moscow_area_id,
        'period': search_period,
        'per_page': per_page
    }

    while page < total_pages:
        params['page'] = page
        response = requests.get(url, params=params)
        response.raise_for_status()
        hh_vacancies = response.json()
        if page == 0:
            vacancies_found = hh_vacancies['found']
        vacancies.extend(hh_vacancies['items'])
        total_pages = hh_vacancies['pages']
        page += 1
    return vacancies, vacancies_found


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if salary and salary['currency'] == 'RUR':
        return predict_salary(salary['from'], salary['to'])


def get_hh_statistics(languages):
    statistics = {}
    for language in languages:
        vacancies, vacancies_found = get_hh_vacancies(language)
        vacancies_processed = 0
        total_salary = 0

        for vacancy in vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                vacancies_processed += 1
                total_salary += salary

        if vacancies_processed:
            average_salary = int(total_salary / vacancies_processed)
        else:
            average_salary = 0

        statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return statistics


def get_sj_vacancies(language, secret_key):
    vacancies = []
    page = 0
    has_more = True
    url = 'https://api.superjob.ru/2.0/vacancies/'
    moscow_area_id = 4
    category_id = 48
    per_page = 100
    vacancies_found = 0
    headers = {
        'X-Api-App-Id': secret_key
    }
    params = {
        'keyword': language,
        'town': moscow_area_id,
        'catalogues': category_id,
        'count': per_page
    }

    while has_more:
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        sj_vacancies = response.json()
        if page == 0:
            vacancies_found = sj_vacancies['total']
        vacancies.extend(sj_vacancies['objects'])
        page += 1
        has_more = sj_vacancies['more']
    return vacancies, vacancies_found


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_sj_statistics(languages, secret_key):
    statistics = {}
    for language in languages:
        vacancies, vacancies_found = get_sj_vacancies(language, secret_key)
        vacancies_processed = 0
        total_salary = 0

        for vacancy in vacancies:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                vacancies_processed += 1
                total_salary += salary

        if vacancies_processed:
            average_salary = int(total_salary / vacancies_processed)
        else:
            average_salary = 0

        statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return statistics


def print_statistics(title, statistics):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for language, stats in statistics.items():
        table_data.append([
            language,
            stats['vacancies_found'],
            stats['vacancies_processed'],
            stats['average_salary'] if stats['average_salary'] else 'N/A'
        ])
    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    load_dotenv()
    sj_api_key = os.environ["SJ_API_KEY"]
    languages = ['Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'Go', '1С', 'PHP']

    hh_statistics = get_hh_statistics(languages)
    print_statistics('HeadHunter Moscow', hh_statistics)

    sj_statistics = get_sj_statistics(languages, sj_api_key)
    print_statistics('SuperJob Moscow', sj_statistics)


if __name__ == '__main__':
    main()
