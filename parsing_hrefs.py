import json
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

INPUT_FILE_NAME = "investfunds.ru-hrefs" + ".csv"
OUTPUT_FILE_NAME = "investfunds.ru-PIFs" + ".csv"
PROXY_LIST = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"


def parsing_hrefs():
    # если хотим использовать свежий список прокси
    # r = requests.get(PROXY_LIST)
    # if r.status_code - 200:
    #   print(f"ERROR: cannot create connection to proxy_list by href {PROXY_LIST}")
    #   return None

    r = open("proxylist.txt")
    proxy_list = json.loads(r.read())

    head = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; AOL 9.0; Windows NT 5.1)'}

    result_list = {'href': [], 'Название': [], 'УК': [], 'Объект': [],
                   'Специализация': [], 'География': [], 'Валюта': [], 'Пайщики': [],
                   'Взнос': [], 'пВзнос': [], 'Вознаграждение': [], 'Депозитарию': [], 'Прочие': [],
                   'Пай': [], '6месП': [], '1годП': [], '3годаП': [], '5летП': [],
                   'СЧА': [], '6месС': [], '1годС': [], '3годаС': [], '5летС': [],
                   'кШарпа': [], 'кСортино': [], 'Волатильность': [], 'VaR': [], 'alpha': [], 'beta': [], 'R2': [],
                   }

    # вбиваем ссылки в results_list
    href_list = pd.read_csv(INPUT_FILE_NAME, sep=';').to_dict(orient='list')
    result_list['href'].extend(href_list['href'])

    # смотрим информацию по ссылкам
    i = 0
    num_of_proxies = len(proxy_list['data'])
    for href in href_list['href']:

        # создаём proxy-подключение
        proxy_json_item = proxy_list['data'][i % num_of_proxies]
        proxy = {
            proxy_json_item['protocols'][0]:
                'http://' + proxy_json_item['ip'] + ':' + proxy_json_item['port'],
            # 'http': 'http://195.9.149.198:8081',
        }
        page = requests.get(href, headers=head, proxies=proxy)
        if page.status_code != 200:
            print(f"ERROR: cannot create connection to {href}")
            return result_list

        soup = bs(page.text, "html.parser")
        # 1 общая информация
        title = soup.find('h1', class_='widget_info_ttl')
        result_list['Название'].append(title.text
                                       .split('(', 1)[0])
        result_list['УК'].append(title.text
                                 .split('(', 1)[1]
                                 .split(')', 1)[0])
        print(i, '\t', result_list['УК'][i], " — ", result_list['Название'][i])

        list_info = soup.find('div', class_='list_info widget full')\
            .find_all('div', class_='flex_row_col')
        for item in list_info:
            match item.contents[1].text:
                case "объект инвестирования":
                    result_list['Объект'].append(item.contents[3].text)
                case "специализация":
                    result_list['Специализация'].append(item.contents[3].text)
                case "география":
                    result_list['География'].append(item.contents[3].text)

        if len(result_list['Объект']) < i+1:
            result_list['Объект'].append(None)
        if len(result_list['Специализация']) < i+1:
            result_list['Специализация'].append(None)
        if len(result_list['География']) < i + 1:
            result_list['География'].append(None)

        common_info = soup.find(attrs={"data-modul": "info"})\
            .find_all('li', class_='item')
        for item in common_info:
            match item.contents[1].text.split(' ', 1)[0]:
                case "Валюта":
                    result_list['Валюта'].append(item.contents[3].text)
                case "Пайщики":
                    result_list['Пайщики'].append(int(item.contents[3].text
                                                      .replace(' ', '')))
                    
        if len(result_list['Валюта']) < i+1:
            result_list['Валюта'].append(None)
        if len(result_list['Пайщики']) < i+1:
            result_list['Пайщики'].append(np.nan)
            pass

        # 2 Оплата, условия
        conditions_info = soup.find(attrs={"data-modul": "investment"})\
            .find_all('li', class_='item')
        for item in conditions_info:
            if len(item.contents) > 3:  # обход проблемы несоответствия "вознаграждение депозитарию"
                match item.contents[1].text:
                    case "Первоначальный взнос":
                        result_list['Взнос'].append(int(item.contents[3].text
                                                        .rsplit(' ', 1)[0]
                                                        .replace(' ', '')))
                    case "Последующий взнос":
                        result_list['пВзнос'].append(int(item.contents[3].text
                                                         .rsplit(' ', 1)[0]
                                                         .replace(' ', '')))
                    case "Вознаграждение УК":
                        result_list['Вознаграждение'].append(float(item.contents[3].text
                                                                   .split(r'%', 1)[0]
                                                                   .translate({ord(' '): None, ord('\n'): None})))
                    case "Вознаграждение депозитарию и др.":
                        result_list['Депозитарию'].append(float(item.contents[3]
                                                                .text.split(r'%', 1)[0]
                                                                .translate({ord(' '): None, ord('\n'): None})))
                    case "Прочие расходы":
                        result_list['Прочие'].append(float(item.contents[3].text
                                                           .split(r'%', 1)[0]
                                                           .translate({ord(' '): None, ord('\n'): None})))

        if len(result_list['пВзнос']) < i+1:
            result_list['пВзнос'].append(np.nan)
        if len(result_list['Вознаграждение']) < i+1:
            result_list['Вознаграждение'].append(np.nan)
        if len(result_list['Депозитарию']) < i+1:
            result_list['Депозитарию'].append(np.nan)
        if len(result_list['Прочие']) < i+1:
            result_list['Прочие'].append(np.nan)
            pass

        # 3 пай и СЧА тянем одновременно по проверке пая (2 известных варианта)
        share_bs = soup.find('tr', class_='field_fixed_0 rublast')
        assets_bs = soup.find('tr', class_='field_fixed_1 rublast')
        if share_bs is not None:
            result_list['Пай'].append(float(share_bs.contents[3].text))
            result_list['СЧА'].append(float(assets_bs.contents[3].text
                                            .replace(' ', '')))

            share_percents = soup.find('tr', class_='field_scroll_0 rublast')
            assets_percents = soup.find('tr', class_='field_scroll_1 rublast')
        else:
            share_bs = soup.find('tr', class_='field_fixed_0 otherCurrencylast')
            assets_bs = soup.find('tr', class_='field_fixed_1 otherCurrencylast')
            if share_bs is not None:
                result_list['Пай'].append(float(share_bs.contents[3].text))
                result_list['СЧА'].append(float(assets_bs.contents[3].text
                                                .replace(' ', '')))
                share_percents = soup.find('tr', class_='field_scroll_0 otherCurrencylast')
                assets_percents = soup.find('tr', class_='field_scroll_1 otherCurrencylast')
        # 4 Заполняем проценты по 6 мес -- 5 лет
        if share_bs is not None:
            if share_percents.contents[7].text != '—':
                result_list['6месП'].append(float(share_percents.contents[7].text
                                                  .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['6месП'].append(np.nan)
            if share_percents.contents[9].text != '—':
                result_list['1годП'].append(float(share_percents.contents[9].text
                                                  .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['1годП'].append(np.nan)
            if share_percents.contents[11].text != '—':
                result_list['3годаП'].append(float(share_percents.contents[11].text
                                                   .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['3годаП'].append(np.nan)
            if share_percents.contents[13].text != '—':
                result_list['5летП'].append(float(share_percents.contents[13].text
                                                  .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['5летП'].append(np.nan)

            if assets_percents.contents[7].text != '—':
                result_list['6месС'].append(float(assets_percents.contents[7].text
                                                  .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['6месС'].append(np.nan)
            if assets_percents.contents[9].text != '—':
                result_list['1годС'].append(float(assets_percents.contents[9].text
                                                  .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['1годС'].append(np.nan)
            if assets_percents.contents[11].text != '—':
                result_list['3годаС'].append(float(assets_percents.contents[11].text
                                                   .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['3годаС'].append(np.nan)
            if assets_percents.contents[13].text != '—':
                result_list['5летС'].append(float(assets_percents.contents[13].text
                                                  .translate({ord(' '): None, ord('%'): None})))
            else:
                result_list['5летС'].append(np.nan)
        # в случае третьего варианта
        else:
            result_list['Пай'].append(np.nan)
            result_list['6месП'].append(np.nan)
            result_list['1годП'].append(np.nan)
            result_list['3годаП'].append(np.nan)
            result_list['5летП'].append(np.nan)
            
            result_list['СЧА'].append(np.nan)
            result_list['6месС'].append(np.nan)
            result_list['1годС'].append(np.nan)
            result_list['3годаС'].append(np.nan)
            result_list['5летС'].append(np.nan)

        # 5 Коэффициенты
        coefficients_list = soup.find(attrs={"data-modul": "coefficient"})
        if coefficients_list is not None:
            coefficients_list = coefficients_list.find_all('td', class_='text_center')

            result_list['кШарпа'].append(float(coefficients_list[0].text))
            result_list['кСортино'].append(float(coefficients_list[2].text))
            result_list['Волатильность'].append(float(coefficients_list[4].text
                                                      .replace(r'%', '')))
            result_list['VaR'].append(float(coefficients_list[6].text
                                            .replace(r'%', '')))
            result_list['alpha'].append(float(coefficients_list[8].text))
            result_list['beta'].append(float(coefficients_list[10].text))
            result_list['R2'].append(float(coefficients_list[12].text
                                           .replace(r'%', '')))
        else:
            result_list['кШарпа'].append(np.nan)
            result_list['кСортино'].append(np.nan)
            result_list['Волатильность'].append(np.nan)
            result_list['VaR'].append(np.nan)
            result_list['alpha'].append(np.nan)
            result_list['beta'].append(np.nan)
            result_list['R2'].append(np.nan)

        i += 1
    return result_list


if __name__ == '__main__':
    file = pd.DataFrame(data=parsing_hrefs())
    file.to_csv(OUTPUT_FILE_NAME, sep=';', encoding="cp1251")