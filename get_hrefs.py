# This is a sample Python script.
import datetime

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from datetime import datetime
import time

FILE_NAME = "investfunds_hrefs//investfunds.ru-PIF_" + str(datetime.now().date()) + '_' + \
            str(datetime.now().time())[:8].replace(':','-') + ".csv"
URL_TEMPLATE = "https://investfunds.ru/fund-rankings/fund-yield/"
URL_SITE = "https://investfunds.ru"


def get_hrefs():
    r = requests.get(URL_TEMPLATE)
    if r.status_code - 200:
        print(f"ERROR: cannot create connection to {URL_TEMPLATE}")
        return None

    # находим все фонды
    soup = bs(r.text, "html.parser")
    shown_elements = soup.select('tr[class*="js_show_srch_text js_show_srch_text_ready field_fixed"]')
    hidden_elements = soup.select('tr[class*="js_show_more_wrapper js_show_srch_text hidden field_fixed"]')
    all_elements = shown_elements + hidden_elements
    result_list = set()

    for each_part in all_elements:
        if each_part.find('a'):
            href = each_part.a['href']
            result_list.add(URL_SITE + href)

    result_list_dict = {'href': list(result_list)}
    return result_list_dict


if __name__ == '__main__':
    file = pd.DataFrame(data=get_hrefs())
    file.to_csv(FILE_NAME, sep=';', index=False)