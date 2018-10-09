import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def build_driver(headless=True):
    """
    Build a selenium driver for the desired browser with its parameters
    """
    # Build Firefox profile
    options = Options()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Firefox(firefox_options=options)
    driver.set_page_load_timeout(90)

    return driver


def check_exists_by_xpath(driver, xpath):
    """check if an element exists by its xpath"""
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def wait_by_id(driver, id, retries=20):
    """
    Wait for element to load by ID
    """
    try:
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.ID, id)))
    except Exception:
        print(f"Unable to find element {id} in page")
        return False
    return True


def iter_dom(driver, xpath):
    """
    Iterate over dom elements to avoid losing focus.
    """
    def get_next_element(elems, idx):
        for i, element in enumerate(elems):
            if i == idx:
                return element

    current_idx = 0
    has_elements = True
    while has_elements:
        elements = driver.find_elements_by_xpath(xpath)
        try:
            elem = get_next_element(elements, current_idx)
            if elem:
                yield elem
        except Exception as e:
            elements = driver.find_elements_by_xpath(xpath)
            elem = get_next_element(elements, current_idx)
            if elem:
                yield elem

        if elem:
            current_idx += 1
        else:
            has_elements = False


def wait_by_xpath(driver, xpath, retries=20):
    """
    Wait for xpath element to load
    """
    try:
        # element = WebDriverWait(driver, retries).until(
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
    except Exception:
        print(f"Unable to find element {xpath} in page")


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
    coaster_infos['open'] = driver.find_element_by_xpath('//*[@id="feature"]/a').get_attribute('innerHTML').lower() == "ouvert"
    coaster_infos['opening_date'] = re.findall('\d{1,2}\/\d{1,2}\/\d{4}', driver.find_element_by_xpath('//*[@id="feature"]').text)[0]

    # Builder / Model
    make_model = driver.find_element_by_xpath('//*[@id="feature"]/div[2]').find_elements_by_css_selector('a')
    maker = make_model[0]
    model = make_model[1:]
    coaster_infos['maker'] = maker.get_attribute('innerHTML')
    coaster_infos['maker_page'] = maker.get_attribute('href')
    coaster_infos['model'] = ', '.join([i.get_attribute('innerHTML') for i in model])
    
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
    details = driver.find_elements_by_xpath('//*[@id="article"]/div/section[4]/table/tbody/tr')
    for tr in details:
        k = tr.find_elements_by_css_selector('td')[0].get_attribute('innerHTML')
        v = tr.find_elements_by_css_selector('td')[1].get_attribute('innerHTML')
        if k.lower() == 'installer:':
            coaster_infos['Installer'] = tr.find_element_by_css_selector('a').get_attribute('text')
            coaster_infos['Installer_page'] = tr.find_element_by_css_selector('a').get_attribute('href')
        else:
            coaster_infos[k] = v

    driver.close()
    return coaster_infos


if __name__ == '__main__':
    driver = build_driver(headless=False)
    search = 'shambhala'
    print(build_coaster(driver, search))
    driver.close()
