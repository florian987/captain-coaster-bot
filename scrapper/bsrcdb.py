import re
import urllib3

from bs4 import BeautifulSoup
try:
    from bot.scrapper.selen_helper import build_driver, wait_by_xpath
except ModuleNotFoundError:
    from selen_helper import build_driver, wait_by_xpath


def build_coaster(search):
    url = 'https://rcdb.com'
    http = urllib3.PoolManager()
    reponse = http.request('GET', f'{url}/qs.htm?qs={search}')
    soup = BeautifulSoup(reponse.data, 'html.parser')

    coaster_infos = {}


    # Get 'feature' div
    feature = soup.find('div', {'id': 'feature'})
    scroll = feature.find('div', {'class': 'scroll'})
    coaster_infos['name'] = scroll.find('h1').text  # Coaster name
    coaster_infos['park'] = scroll.find('a').text
    # Build Location
    loc = []
    for link in scroll.findAll('a')[1:]:
        loc.append(link.text)
    coaster_infos['location'] = ', '.join(loc)
    # Get operating
    opening_dates = feature.find_next('a').text

    print(coaster_infos)
    print(opening_dates)
    






    # Builder / Model
    make_model = driver.find_element_by_xpath(
        '//*[@id="feature"]/div[2]').find_elements_by_css_selector('a')
    maker = make_model[0]
    model = make_model[1:]
    coaster_infos['maker'] = maker.get_attribute('innerHTML')
    coaster_infos['maker_page'] = maker.get_attribute('href')
    coaster_infos['model'] = ', '.join(
        [i.get_attribute('innerHTML') for i in model])

    # Tracks
    tracks = driver.find_elements_by_xpath(
        '//*[@id="statTable"]/tbody/tr'
    )
    for i in tracks:
        k = i.find_element_by_css_selector('th').get_attribute('innerHTML')
        v = i.find_element_by_css_selector('td').get_attribute('innerHTML')
        if k is not None:
            innerHTML = BeautifulSoup(v, 'html.parser')
            if bool(innerHTML.find()):
                v = []
                for item in innerHTML.find_all('a'):
                    v.append(item.getText())
            coaster_infos[k] = v

    # Details
    details = driver.find_elements_by_xpath(
        '//*[@id="article"]/div/section[4]/table/tbody/tr')
    for tr in details:
        k = tr.find_elements_by_css_selector('td')[0].get_attribute('innerHTML')
        v = tr.find_elements_by_css_selector('td')[1].get_attribute('innerHTML')
        if k.lower() == 'installer:':
            coaster_infos['Installer'] = tr.find_element_by_css_selector(
                'a').get_attribute('text')
            coaster_infos['Installer_page'] = tr.find_element_by_css_selector(
                'a').get_attribute('href')
        else:
            coaster_infos[k] = v

    return coaster_infos


if __name__ == '__main__':
    search = 'shambhala'
    print(build_coaster(search))
