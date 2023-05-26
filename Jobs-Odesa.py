# https://habr.com/ru/articles/568334/
import datetime

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from datetime import datetime

FILE_NAME = "Jobs-Odesa.csv"
URL_TEMPLATE = "https://www.work.ua/ru/jobs-odesa/?page=2"


def parsing():
    r = requests.get(URL_TEMPLATE)
    print(r.status_code)

    result_list = {'href': [], 'title': [], 'old': [], 'condition': []}
    soup = bs(r.text, "html.parser")
    vacancies_name = soup.find_all('div', class_='card card-hover card-visited wordwrap job-link js-hot-block')
    #vacancies_text = soup.find_all('p', class_='overflow text-muted add-top-sm cut-bottom')
    for vacancy in vacancies_name:
        vacancy_title = vacancy.a['title'].rsplit(',', 1)
        result_list['title'].append(vacancy_title[0])
        result_list['old'].append(vacancy_title[1][12:])
        result_list['href'].append("https://www.work.ua" + vacancy.a['href'])
        result_list['condition'].append(vacancy.findNext('p', class_='overflow text-muted add-top-sm cut-bottom')\
                                    .text.split('\n',2)[1][12:])  # обрезаем по \n[text]\n и убираем 12 пробелов в начале

    return result_list

    #print(vacancies_name)
    #print(type(soup))
    #print(type(vacancies_name))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    file = pd.DataFrame(data=parsing())
    file.to_csv(FILE_NAME,sep=';')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
