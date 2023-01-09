import os
import requests

from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(payment_from, payment_to):
    average_salary = 0

    if payment_from and payment_to:
        average_salary = (payment_from+payment_to)/2

    if payment_from and not payment_to:
        average_salary = 1.2*payment_from

    if not payment_from and payment_to:
        average_salary = 0.8*payment_to

    return average_salary


def get_hh_salary_statistics(url, vacancy, period):
    page = 0
    pages = 1
    city_code = 1
    vacancies_found = 0
    vacancies_processed = 0
    average_salary = 0
    params = {
            "text": vacancy,
            "area": city_code,
            "period": period,
            "only_with_salary": True,
            "page": page
    }

    while page <= pages:
        response = requests.get(url, params)
        response.raise_for_status()
        response_content = response.json()

        pages = response_content["pages"]
        vacancies_found = response_content["found"]

        for vacancy in response_content['items']:
            if vacancy["salary"]["currency"] == 'RUR':
                payment_from = vacancy['salary']['from']
                payment_to = vacancy['salary']['to']
                average_salary += predict_rub_salary(payment_from, payment_to)
                vacancies_processed += 1
        page += 1
        params["page"] = page
    if vacancies_processed:
        average_salary = int(average_salary/vacancies_processed)

    return {'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary}


def get_sj_salary_statistics(url, token, vacancy, period):
    headers = {"X-Api-App-Id": token}
    page = 0
    pages = 1
    params = {
        "town": "Москва",
        "period": period,
        "keyword": vacancy,
        "currency": "rub",
        "page": page,
        "count": 100
    }
    average_salary = 0
    vacancies_processed = 0
    vacancies_found = 0
    while page <= pages:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        response_content = response.json()
        vacancies_found = response_content["total"]
        pages = vacancies_found/100
        for vacancy in response_content["objects"]:
            if vacancy["currency"] == 'rub':
                payment_from = vacancy['payment_from']
                payment_to = vacancy['payment_to']
                average_salary += predict_rub_salary(payment_from, payment_to)
                vacancies_processed += 1
        page += 1
        params["page"] = page
    if vacancies_processed:
        average_salary = int(average_salary/vacancies_processed)

    return {'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary}


def create_table(salary_statistics, title):
    column_names = [["Язык программирования",
                     "Вакансий найдено",
                     "Вакансий обработано",
                     "Средняя зарплата"]]
    for language, statistics in salary_statistics.items():
        vacancy_statistics = [
            language,
            statistics["vacancies_found"],
            statistics["vacancies_processed"],
            statistics["average_salary"]
        ]
        column_names.append(vacancy_statistics)
    table_instance = AsciiTable(column_names, vacancy_statistics)
    return table_instance.table


def main():
    load_dotenv()
    token = os.getenv('SUPER_JOB_SECRET_KEY')
    hh_url = "https://api.hh.ru/vacancies"
    sj_url = "https://api.superjob.ru/2.0/vacancies/"

    programming_languages = [
        "C",
        "C++",
        "C#",
        "Go",
        "Java",
        "JavaScript",
        "Objective-C",
        "PHP",
        "Python",
        "Ruby",
        "Scala",
        "Swift",
        "Typescript",
    ]

    hh_salary_statistics = dict()
    sj_salary_statistics = dict()
    period = 10
    for language in programming_languages:
        vacancy_keyword = f"Программист {language}"
        hh_salary_statistics[language] = (
            get_hh_salary_statistics(hh_url, vacancy_keyword, period)
        )
        sj_salary_statistics[language] = (
            get_sj_salary_statistics(sj_url,
                                     token,
                                     vacancy_keyword,
                                     period)
        )

    print(create_table(hh_salary_statistics, "HeadHunter Moscow"))
    print(create_table(sj_salary_statistics, "SuperJob Moscow"))

if __name__ == '__main__':
    main()
