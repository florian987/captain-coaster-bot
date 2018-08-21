# -*- coding: utf-8 -*-

# import pickle
# import traceback
import json
import logging
import os
import shutil
import time
import urllib

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

log = logging.getLogger(__name__)

# Credentials

google_email = "adelargem@gmail.com"
google_password = "AerhEHa3654G!gre"

script_dir = os.path.dirname(os.path.realpath(__file__))
download_dir = os.path.join(script_dir, "downloads")
log_dir = os.path.join(script_dir, "logs")
gecko_log_path = os.path.join(log_dir, "geckodriver.log")


needed_dirs = [
    download_dir,
    log_dir
]


def build_driver(browser="Chrome", headless=True, proxy=None):
    """
    Build a selenium driver for the desired browser with its parameters
    """
    # TODO Implement firefox, waiting for selenium 3.14.0 to fix timeout

    # PROXY = "fw_in.bnf.fr:8080"

    # Create needed directories if not existing
    for directory in needed_dirs:
        create_dirs(directory)

    # Set Chrome browser settings
    if browser == "Chrome":
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        })

        if headless:
            options.add_argument('headless')
            # Not tested
            options.add_argument('disable-gpu')

            # download_path = download_dir

        # Build Chrome driver
        driver = webdriver.Chrome(chrome_options=options)

        # Add devtools command to allow download
        driver.execute_cdp_cmd(
            'Page.setDownloadBehavior', 
            {'behavior': 'allow', 'downloadPath': download_dir})

    # Handle Firefox profile
    elif browser == "Firefox":

        # Build Firefox profile
        profile = webdriver.FirefoxProfile()
        profile.set_preference(
            'browser.download.folderList', 2)  # custom location
        profile.set_preference(
            'browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.download.dir', download_dir)
        profile.set_preference('browser.download.downloadDir', download_dir)
        profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk', 'application/zip')
        profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk',
            'application/octet-stream')

        # Proxy settings
        if proxy:
            firefox_proxy = Proxy({
                'proxyType': ProxyType.MANUAL,
                'httpProxy': settings.PROXY,
                'ftpProxy': settings.PROXY,
                'sslProxy': settings.PROXY,
                'noProxy': ''  # set this value as desired
            })

            driver = webdriver.Firefox(
                profile, proxy=firefox_proxy, 
                log_path=gecko_log_path)  # Ajout du proxy

        else:
            # Build Firefox driver without proxy
            driver = webdriver.Firefox(profile, log_path=gecko_log_path)

    # Set global driver settings
    # driver.implicitly_wait(60)
    driver.set_page_load_timeout(90)

    return driver


def iter_dom(driver, xpath):
    """
    Iterate over dom elements to avoid losing focus.
    """
    def get_next_element(elems, idx):
        for i, element in enumerate(elems):
            # print("get elem : %s / %s / %s" % (i, idx, element))
            if i == idx:
                return element

    current_idx = 0
    has_elements = True
    while has_elements:
        elements = driver.find_elements_by_xpath(xpath)
        # print(driver.current_url)
        try:
            elem = get_next_element(elements, current_idx)
            # print("Try1: %s / %s" % (current_idx, elem))
            if elem:
                yield elem
        except Exception as e:
            elements = driver.find_elements_by_xpath(xpath)
            elem = get_next_element(elements, current_idx)
            # print("Try2: %s / %s / %s" % (current_idx, elem, e))
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


def wait_by_css(driver, css, retries=20):
    """
    Wait for css element to load
    """
    try:
        # element = WebDriverWait(driver, retries).until(
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css)))
    except Exception:
        print(f"Unable to find element {css} in page")


def wait_by_id(driver, id, retries=20):
    """
    Wait for element to load by ID
    """
    try:
        # element = WebDriverWait(driver, retries).until(
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.ID, id)))
    except Exception:
        print(f"Unable to find element {id} in page")


def check_exists_by_xpath(driver, xpath):
    """
    check if an element exists by its xpath
    """
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def create_dirs(directory):
    """
    Ensure a directory exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_img(url, dest=None):
    """
    Download an image weither specifying or not its destination.

    Register using filename from url. In cwd if dest is not set
    """
    # Set filename from url
    url_filename = url.split('/')[-1]

    # Download in current working directory if dest is not set
    if dest is None:
        urllib.request.urlretrieve(url, url_filename)
    # Download in specified directory
    else:
        # Set destination filename if not provided in dest
        if "." not in dest.split('/')[-1]:
            file_dest = os.path.join(dest, url_filename)
        else:
            file_dest = dest

        if not os.path.isfile(file_dest):  # Download if not exists
            urllib.request.urlretrieve(url, file_dest)


def build_cars_list(driver):
    """
    Build cars list from datapacks page
    """

    # Initialize cars array
    cars = []

    site_url = "https://virtualracingschool.appspot.com/#/DataPacks/"

    print("- Retrieving cars list ...")
    driver.get(site_url)

    # Wait JavaScript to load cars table
    wait_by_xpath(driver, "//table[@data-vrs-widget='tableWrapper']/tbody/tr")

    # Retrieve cars table
    car_row = driver.find_elements_by_xpath(
        "//table[@data-vrs-widget='tableWrapper']/tbody/tr"
    )

    # Iterate over table car_elems
    for car_elem in car_row:

        # Set premium status depending of style display
        if ("visible" in car_elem
                .find_element_by_class_name('blue').get_attribute('style')):
            car_premium = True
        else:
            car_premium = False

        # Get car ID
        node_span = car_elem.find_element_by_css_selector(
            "p:nth-of-type(1)"
        ).get_attribute("innerHTML")

        soup = BeautifulSoup(node_span, "html.parser")
        for span in soup.findAll(
                "span", attrs={"data-vrs-widget-field": "packIdElement"}
        ):
            node_id = span.text

        # Create car dict
        car = {}
        car['serie'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(1) img').get_attribute('title')
        car['serie_img_url'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(1) img').get_attribute('src')
        car['serie_img_name'] = car['serie_img_url'].split('/')[-1]
        car['img_url'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(2) img').get_attribute('src')
        car['img_name'] = car['img_url'].split('/')[-1]
        car['name'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(2) img').get_attribute('title')
        car['season'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(3)').text
        car['author'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(4) img').get_attribute('title')
        car['img_author'] = car_elem.find_element_by_css_selector(
            'td:nth-of-type(4) img').get_attribute('src')
        car['id'] = node_id
        car['url'] = site_url + node_id
        car['premium'] = car_premium
        car['season_path'] = os.path.join(download_dir, car['season'])
        car['serie_path'] = os.path.join(car['season_path'], car['serie'])
        car['car_path'] = os.path.join(car['serie_path'], car['name'])

        cars.append(car)  # Add car to cars list

    return cars  # Return cars list


def authenticate(driver):
    """
    Authenticate using a Google account and return a boolean
    """
    driver.get("https://virtualracingschool.appspot.com/#/DataPacks")
    time.sleep(2)

    try:
        # Open menu
        wait_by_css(driver, ".button-collapse")
        driver.find_element_by_class_name(".button-collapse").click()
        time.sleep(2)

        # Derouler menu
        driver.find_element_by_css_selector(
            'i.material-icons:nth-child(4)'
        ).click
        time.sleep(2)

        # Click login button
        driver.find_element_by_css_selector(
            'li.active > div:nth-child(2) > ul:nth-child(1) > li:nth-child(5)'
            ' > a:nth-child(1) > span:nth-child(2)'
        ).click

        # click Login with google
        wait_by_id(driver, '#gwt-debug-googleLogin')
        driver.find_element_by_id('#gwt-debug-googleLogin').click

        # Type login
        wait_by_id(driver, 'identifierId')
        driver.find_element_by_id('identifierId').send_keys(google_email)
        driver.find_element_by_css_selector(
            '#identifierNext > div:nth-child(2)'
        ).click()

        # Type password
        wait_by_css(
            driver,
            '#password > div:nth-child(1) > div:nth-child(1) '
            '> div:nth-child(1) > input:nth-child(1)'
        )

        driver.find_element_by_css_selector(
            '#password > div:nth-child(1) > div:nth-child(1)'
            '> div:nth-child(1) > input:nth-child(1)'
        ).send_keys(google_password)

        driver.find_element_by_css_selector(
            '#passwordNext > div:nth-child(2)'
        ).click()

        return True

    except Exception:
        return False


def build_datapacks_infos(driver, cars_list, premium=False):
    """
    Retrieve all available datapacks with infos and files
    """

    premium = authenticate(driver)

    if not premium:  # Define list to iterate over
        cars_list = [item for item in cars_list if not item['premium']]

    for car in cars_list:  # Build datapacks

        car['datapacks'] = []  # Initialize datapacks list

        # Only iterate over free cars
        if not car['premium']:

            print(f"|_ Building {car['serie']} - {car['name']} datapacks")

            driver.get(car['url'])  # Load car URL and wait Js load
            wait_by_xpath(driver, f"//p[@class='base-info' "
                          "and text()=\"{car['name']}\"]")

            # Iterate over DataPacks tables TR
            car_elems = iter_dom(driver, "//table[@data-vrs-widget="
                                 "'DataPackWeeksTable']/tbody/tr")
            for car_elem in car_elems:

                datapack = {}  # Create datapack dict
                datapack_path = ''

                try:  # Build datapack
                    datapack['track'] = car_elem.find_elements_by_css_selector(
                        "td:nth-of-type(2) img"
                    )[0].get_attribute('title')

                    datapack['fastest_laptime'] = car_elem.find_elements_by_css_selector(
                        "td:nth-of-type(3) div span:nth-of-type(1) span"
                    )[0].get_attribute('title')

                    datapack['time_of_day'] = (car_elem.find_elements_by_css_selector(
                        "td:nth-of-type(4) div span:nth-of-type(1) span"
                    )[0].get_attribute('title'))

                    datapack['track_state'] = car_elem.find_elements_by_css_selector(
                        "td:nth-of-type(4) div span:nth-of-type(2) span"
                    )[0].get_attribute('title')

                    # If datapack is not empty
                    if datapack['fastest_laptime'] != "":

                        # Open permalink box
                        car_elem.find_element_by_css_selector(
                            "td:nth-of-type(6) a:nth-of-type(3)"
                        ).click()

                        # Get datapack permalink
                        datapack['url'] = driver.find_element_by_css_selector(
                            ".gwt-TextBox"
                        ).get_attribute('value')

                        # Close modal
                        driver.find_element_by_css_selector(
                            ".KM1CN4-a-h a"
                        ).click()

                    car['datapacks'].append(datapack)

                except Exception as e:
                    # print('ERR', e)
                    # traceback.print_stack()
                    pass

            for datapack in car['datapacks']:
                datapack['files'] = []

                datapack_path = os.path.join(  # Build desired paths
                    car['car_path'], datapack['track'])

                create_dirs(datapack_path)  # Create paths if needed

                if "url" in datapack:  # If datapack has url

                    driver.get(datapack['url'])  # Load datapack url
                    wait_by_xpath(driver, f"//span[text()=\""  # Wait page
                                  "{datapack['track']}\"]")
                    # print('page: ' + driver.current_url)

                    # Iterate over files
                    file_elements = iter_dom(driver, "//li[@data-vrs-widget="
                                             "'LIWrapper']/div/div/form/div/a")

                    for file_element in file_elements:
                        filetype = {  # Define extensions dict
                            "olap": "hotlap",
                            "blap": "bestlap",
                            "rpy": "replay",
                            "zip": "replay",
                            "sto": "setup"
                        }

                        file = {}  # Create file dict

                        # Set file attributes
                        file['name'] = file_element.get_attribute('text')
                        file_extension = file['name'].split('.')[-1]
                        file["type"] = filetype.get(file_extension, "unknown")
                        filepath_temp = os.path.join(
                            download_dir, file['name']
                        )
                        file['path'] = os.path.join(
                            datapack_path, file['name']
                        )

                        # Download Car image
                        download_img(car['img_url'], car['car_path'])
                        # Download Serie image
                        download_img(car['serie_img_url'], car['serie_path'])

                        # Download datapack file if not present
                        if not os.path.isfile(file['path']):
                            try:
                                file_element.click()
                            except Exception:
                                print("Can not click")

                            # Close modal License box if opened
                            try:
                                ok_button = driver.find_element_by_xpath(
                                    '/html/body/div[7]/div/div/div[3]/a[2]'
                                )
                                ok_button.click()
                            except Exception as e:
                                pass

                            sleep_count = 0
                            # Wait file to be downloaded (Chrome)
                            while not (os.path.isfile(filepath_temp) and
                                       sleep_count < 180):
                                # print('wait because part', sleep_count)
                                time.sleep(1)
                                sleep_count += 1

                            shutil.move(filepath_temp, file['path'])

                            # TODO per browser switch
                            # Wait file to be downloaded (Firefox)
                            # sleep_count = 0
                            # while os.path.isfile(filepath_temp + '.part')
                            # and sleep_count < 90:
                            #    print('wait because part', sleep_count)
                            #    time.sleep(1)
                            #    sleep_count += 1

                            # print('DL OK', 'Temp_path: ' + filepath_temp)

                            # Move file
                            # if not os.path.isfile(filepath_temp + '.part')
                            # and os.path.isfile(filepath_temp):
                            #    shutil.move(filepath_temp, file['path'])
                            #
                            #    #time.sleep(5)

                        # Add file to files list
                        datapack['files'].append(file)

    # pickle.dump(cars_list, open(settings.history_file,'wb'))

    with open(os.path.join(download_dir, 'data.json'), 'w') as tempfile:
        json.dump(cars_list, tempfile)

    driver.close()

    return cars_list


if __name__ == '__main__':

    driver = build_driver()
    cars_list = build_cars_list(driver)  # Create cars list
    build_datapacks_infos(driver, cars_list)  # Build cars datapacks

    # with open ('data.json', 'w') as tempfile:
    #    json.dump(cars_list, tempfile)

    # print(json.dumps(cars_list, indent=4))

    # Finaly close the browser
    driver.close()
