import os
import requests

from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_salary(payment_from, payment_to):
    average_salary = 0

    if payment_from and payment_to:
        average_salary = (payment_from+payment_to)/2

    if payment_from and not payment_to:
        average_salary = 1.2*payment_from

    if not payment_from and payment_to:
        average_salary = 0.8*payment_to

    return average_salary


def predict_rub_salary_hh(vacancy):
    payment_from = vacancy['salary']['from']
    payment_to = vacancy['salary']['to']
    currency = vacancy['salary']['currency']

    if not currency == 'RUR':
        return None
    return predict_salary(payment_from, payment_to)


def predict_rub_salary_sj(vacancy):
    payment_from = vacancy['payment_from']
    payment_to = vacancy['payment_to']
    currency = vacancy['currency']

    if not currency == 'rub':
        return None
    return predict_salary(payment_from, payment_to)


def get_hh_salary_statistics(url, vacancy, period):
    page = 0
    pages = 1
    vacancies_found = 0
    vacancies_processed = 0
    average_salary = 0
    params = {
            "text": vacancy,
            "area": 1,
            "period": period,
            "only_with_salary": True,
            "page": page
    }

    while page <= pages:
        response = requests.get(url, params)
        response.raise_for_status()
        pages = response.json()['pages']
        vacancies_found = response.json()['found']

        for vacancy in response.json()['items']:
            if predict_rub_salary_hh(vacancy):
                average_salary += predict_rub_salary_hh(vacancy)
                vacancies_processed += 1
        page += 1
        params["page"] = page
    average_salary = int(average_salary/vacancies_processed)

    return {'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary}


def predict_rub_salary_sj(vacancy):
    payment_from = vacancy['payment_from']
    payment_to = vacancy['payment_to']
    currency = vacancy['currency']

    if not currency == 'rub':
        return None
    return predict_salary(payment_from, payment_to)


def get_sj_salary_statistics(url, token, vacancy, period):
    headers = {"X-Api-App-Id": token}
    page = 0
    pages = 1
    params = {
        "town": "Москва",
        "period": period,
        "keyword": f"Программист",
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
        vacancies_found = response.json()["total"]
        pages = vacancies_found/100
        for vacancy in response.json()["objects"]:
            if predict_rub_salary_sj(vacancy):
                average_salary += predict_rub_salary_sj(vacancy)
                vacancies_processed += 1
        page += 1
        params["page"] = page
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
        column_data = [
            language,
            statistics["vacancies_found"],
            statistics["vacancies_processed"],
            statistics["average_salary"]
        ]
        column_names.append(column_data)
    # print(column_names)
    table_instance = AsciiTable(column_names, title)
    return table_instance.table


def main():
    load_dotenv()
    token = os.getenv('SECRET_KEY')
    url_hh = "https://api.hh.ru/vacancies"
    url_sj = "https://api.superjob.ru/2.0/vacancies/"

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
        vacancy = f"Программист {language}"
        hh_salary_statistics.update(
            {language: get_hh_salary_statistics(url_hh, vacancy, period)}
        )
        sj_salary_statistics.update(
            {language: get_sj_salary_statistics(url_sj,
                                                token,
                                                vacancy,
                                                period)}
        )

    print(create_table(hh_salary_statistics, "HeadHunter Moscow"))
    print(create_table(sj_salary_statistics, "SuperJob Moscow"))

if __name__ == '__main__':
    main()
