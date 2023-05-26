import json
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

# using proxy https://ru.stackoverflow.com/questions/673069/%D0%9E%D1%88%D0%B8%D0%B1%D0%BA%D0%B0-typeerror-nonetype-object-is-not-subscriptable
FILE_NAME = "parsed_funds//investfunds.ru-PIFs_" + str(datetime.now().date()) + '_' + \
            str(datetime.now().time())[:8].replace(':','-') + ".csv"
#URL_TEMPLATE = "https://investfunds.ru/fund-rankings/fund-yield/"
#URL_SITE = "https://investfunds.ru"
PROXY_LIST = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"


def parsing_hrefs():
    '''
    r = requests.get(PROXY_LIST)
    if r.status_code - 200:
        print(f"ERROR: cannot create connection to proxy_list by href {PROXY_LIST}")
        return None
        '''
    r = open("proxylist.txt")
    proxy_list = json.loads(r.read())

    head = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; AOL 9.0; Windows NT 5.1)'}

    result_list = {'href': [], 'Название':[] ,'УК': [], 'Объект': [],
                   'Специализация': [], 'География': [], 'Валюта': [], 'Пайщики': [],
                   'Взнос': [], 'пВзнос': [],'Вознаграждение': [],'Депозитарию': [],'Прочие': [],
                   'Пай': [], '6месП': [], '1годП': [], '3годаП': [], '5летП': [],
                   'СЧА': [], '6месС': [], '1годС': [], '3годаС': [], '5летС': [],
                   'кШарпа': [], 'кСортино': [], 'Волатильность': [], 'VaR': [], 'alpha': [], 'beta': [], 'R2': [],
                   }



    ''' 'Надбавка': [],
                       'кШарпа': [],'кСортино': [], 'Волатильность': [],'VaR': [], 'alpha': [], 'beta': [], 'R2': [],
                       '6месП': [], '1годП': [], '3годаП': [], '5летП': [],
                   'СЧА': [], '6месС': [], '1годС': [], '3годаС': [], '5летС': [],
                      '''


    # вбиваем ссылки в results_list
    href_list = pd.read_csv("investfunds.ru-PIF.csv",sep=';').to_dict(orient='list')
    result_list['href'].extend(href_list['href'])
    # ради забавы выясняем, какие протоколы у нас есть
    temp_set = set()
    for data in proxy_list['data']:
        for protocol in data['protocols']:
            temp_set.add(protocol)

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
        if not page.status_code == 200:
            print(f"ERROR: cannot create connection to {href}")
            return None

        soup = bs(page.text, "html.parser")
        # 1 общая информация
        title = soup.find('h1', class_='widget_info_ttl')
        result_list['Название'].append(title.text.split('(',1)[0])
        result_list['УК'].append(title.text.split('(',1)[1].split(')',1)[0])
        print(i, '\t', result_list['УК'][i], " — ", result_list['Название'][i])

        list_info = soup.find('div', class_='list_info widget full').find_all('div', class_='flex_row_col')
        for item in list_info:
            match item.contents[1].text:
                case "объект инвестирования":
                    result_list['Объект'].append(item.contents[3].text)
                case "специализация":
                    result_list['Специализация'].append(item.contents[3].text)
                case "география":
                    result_list['География'].append(item.contents[3].text)

        if len(result_list['Объект']) < i+1:
            result_list['Объект'].append("Empty")
        if len(result_list['Специализация']) < i+1:
            result_list['Специализация'].append("Empty")
        if len(result_list['География']) < i + 1:
            result_list['География'].append("Empty")

        common_info = soup.find(attrs={"data-modul": "info"}).find_all('li', class_='item')
        for item in common_info:
            match item.contents[1].text.split(' ',1)[0]:
                case "Валюта":
                    result_list['Валюта'].append(item.contents[3].text)
                case "Пайщики":
                    result_list['Пайщики'].append(item.contents[3].text)

        if len(result_list['Валюта']) < i+1:
            result_list['Валюта'].append("Empty")
        if len(result_list['Пайщики']) < i+1:
            result_list['Пайщики'].append(-1)
            pass

        # Оплата, условия
        conditions_info = soup.find(attrs={"data-modul": "investment"}).find_all('li', class_='item')
        for item in conditions_info:
            if len(item.contents) > 3:  # обход проблемы несоответствия "вознаграждение депозитарию"
                match item.contents[1].text:
                    case "Первоначальный взнос":
                        result_list['Взнос'].append(int(item.contents[3].text.split(' ',1)[0]))
                    case "Последующий взнос":
                        result_list['пВзнос'].append(int(item.contents[3].text.split(' ',1)[0]))
                    case "Вознаграждение УК":
                        result_list['Вознаграждение'].append\
                            (float(item.contents[3].text.split(r'%',1)[0].translate({ord(' '): None, ord('\n'): None})))
                    case "Вознаграждение депозитарию и др.":
                        result_list['Депозитарию'].append\
                        (float(item.contents[3].text.split(r'%', 1)[0].translate({' ': '','\n': ''})))
                    case "Прочие расходы":
                        result_list['Прочие'].append\
                            (float(item.contents[3].text.split(r'%', 1)[0].translate({' ': '','\n': ''})))

        if len(result_list['пВзнос']) < i+1:
            result_list['пВзнос'].append(-1)
        if len(result_list['Вознаграждение']) < i+1:
            result_list['Вознаграждение'].append(-1)
        if len(result_list['Депозитарию']) < i+1:
            result_list['Депозитарию'].append(-1)
        if len(result_list['Прочие']) < i+1:
            result_list['Прочие'].append(-1)
            pass
        разобраться        с        глобальной share_percents, assets_percents https://metanit.com/python/tutorial/2.9.php
        # пай и СЧА тянем одновременно по проверке пая (2 известных варианта)
        share_bs = soup.find('tr', class_='field_fixed_0 rublast')
        assets_bs = soup.find('tr', class_='field_fixed_1 rublast')
        if share_bs is not None:
            result_list['Пай'].append(float(share_bs.contents[3].text))
            result_list['СЧА'].append(float(assets_bs.contents[3].text.replace(' ', '')))

            global share_percents, assets_percents
            share_percents = soup.find('tr', class_='field_scroll_0 rublast')
            assets_percents = soup.find('tr', class_='field_scroll_1 rublast')
        else:
            share_bs = soup.find('tr', class_='field_fixed_0 otherCurrencylast')
            assets_bs = soup.find('tr', class_='field_fixed_1 otherCurrencylast')
            if share_bs is not None:
                result_list['Пай'].append(float(share_bs.contents[3].text))
                result_list['СЧА'].append(float(assets_bs.contents[3].text.replace(' ', '')))
                global share_percents, assets_percents
                share_percents = soup.find('tr', class_='field_scroll_0 otherCurrencylast')
                assets_percents = soup.find('tr', class_='field_scroll_1 otherCurrencylast')
        # Заполняем проценты по 6 мес -- 5 лет
        if share_bs is not None:
            if share_percents.contents[7].text != '—':
                result_list['6месП'].append(float(share_percents.contents[7].text.replace('%', '')))
            else:
                result_list['6месП'].append(-1)
            if share_percents.contents[9].text != '—':
                result_list['1годП'].append(float(share_percents.contents[9].text.replace('%', '')))
            else:
                result_list['1годП'].append(-1)
            if share_percents.contents[11].text != '—':
                result_list['3годаП'].append(float(share_percents.contents[11].text.replace('%', '')))
            else:
                result_list['3годаП'].append(-1)
            if share_percents.contents[13].text != '—':
                result_list['5летП'].append(float(share_percents.contents[13].text.replace('%', '')))
            else:
                result_list['5летП'].append(-1)

            if assets_percents.contents[7].text != '—':
                result_list['6месС'].append(float(assets_percents.contents[7].text.replace('%', '')))
            else:
                result_list['6месС'].append(-1)
            if assets_percents.contents[9].text != '—':
                result_list['1годС'].append(float(assets_percents.contents[9].text.replace('%', '')))
            else:
                result_list['1годС'].append(-1)
            if assets_percents.contents[11].text != '—':
                result_list['3годаС'].append(float(assets_percents.contents[11].text.replace('%', '')))
            else:
                result_list['3годаС'].append(-1)
            if assets_percents.contents[13].text != '—':
                result_list['5летС'].append(float(assets_percents.contents[13].text.replace('%', '')))
            else:
                result_list['5летС'].append(-1)
        # в случае третьего варианта
        else:
            result_list['Пай'].append(-1)
            result_list['6месП'].append(-1)
            result_list['1годП'].append(-1)
            result_list['3годаП'].append(-1)
            result_list['5летП'].append(-1)
            
            result_list['СЧА'].append(-1)
            result_list['6месС'].append(-1)
            result_list['1годС'].append(-1)
            result_list['3годаС'].append(-1)
            result_list['5летС'].append(-1)

        # Коэффициенты
        coefficients_list = soup.find(attrs={"data-modul": "coefficient"})
        if coefficients_list is not None:
            coefficients_list = coefficients_list.find_all('tr', class_='item')

            i+=0




        i += 1
    return result_list


if __name__ == '__main__':
    #result = parsing_hrefs()
    j = 1
    file = pd.DataFrame(data=parsing_hrefs())
    file.to_csv(FILE_NAME, sep=';', encoding="cp1251")
