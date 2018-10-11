import re

from bs4 import BeautifulSoup
try:
    from scrapper.selen_helper import build_driver, wait_by_xpath
except ModuleNotFoundError:
    from selen_helper import build_driver, wait_by_xpath
    

def build_coaster(driver, search):
    url = f'https://rcdb.com/qs.htm?qs={search}'
    coaster_infos = {}
    driver.get(url)
    wait_by_xpath(driver, '//*[@id="article"]/div/section[5]')  # Loading

    # Name & location
    main = driver.find_element_by_xpath(
        '//*[@id="feature"]/div[1]'
    )
    # Coaster name
    coaster_infos['name'] = main.find_element_by_css_selector('h1').get_attribute('innerHTML')
    # Location
    sln_location_list = main.find_elements_by_css_selector('a')[1:]
    loc_list = []  # tmplist
    for item in sln_location_list:
        loc_list.append(item.get_attribute('innerHTML'))
    coaster_infos['location'] = ', '.join(loc_list)

    # Park infos
    park_infos = driver.find_element_by_xpath('//*[@id="feature"]/div[1]/a[1]')
    coaster_infos['park'] = park_infos.get_attribute('innerHTML')
    coaster_infos['park_url'] = park_infos.get_attribute('href')

    # Opening status
    coaster_infos['open'] = driver.find_element_by_xpath(
        '//*[@id="feature"]/a').get_attribute('innerHTML').lower() == "ouvert"
    coaster_infos['opening_date'] = re.findall(
        '\d{1,2}\/\d{1,2}\/\d{4}', driver.find_element_by_xpath(
            '//*[@id="feature"]').text)[0]

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
    driver = build_driver(headless=False, log_path='logs/chromedriver.log')
    search = 'shambhala'
    print(build_coaster(driver, search))
