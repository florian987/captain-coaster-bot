# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import shutil
import time
# import pickle
import traceback
import urllib.request

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

log = logging.getLogger(__name__)

# Credentials

google_email = "osmozwareesport@gmail.com"
google_password = "Nj68994455"
google_cookie = {
    'domain': 'virtualracingschool.appspot.com',
    'expiry': 1542742817,
    'httpOnly': False,
    'name': 'JSESSIONID',
    'path': '/',
    'secure': False,
    'value': 'kmNZrVMwsu14bGYm1UkFxA'
}

#
# PATHS
#
script_dir = os.path.dirname(os.path.realpath(__file__))
DL_DIR = os.path.join(script_dir, "downloads")
log_dir = os.path.join(script_dir, "logs")
gecko_log_path = os.path.join(log_dir, "geckodriver.log")
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DL_DIR = os.path.join(ROOT_DIR, 'tmp')

needed_dirs = [
    DL_DIR,
    log_dir
]

#
# SETUP FILES EXTS
#
filetype = {
    "olap": "hotlap",
    "blap": "bestlap",
    "rpy": "replay",
    "zip": "replay",
    "sto": "setup"
}

#
# SELECTORS
#
XPATH = {
    "cars_table": "//table[@data-vrs-widget='tableWrapper']/tbody/tr",
    "login_btn": '//*[@id="gwt-debug-mainWindow"]/div/main/div[2]/div/div/div[2]/a/span',
    "ggl_login_btn": '//*[@id="gwt-debug-googleLogin"]',
    "login_field": '//*[@id="identifierId"]',
    "login_nxt": '//*[@id="identifierNext"]/content/span',
    "passwd_field": '//*[@id="password"]/div[1]/div/div[1]/input',
    "passwd_nxt": '//*[@id="passwordNext"]/content/span',
    "subscr_div": '//*[@id="gwt-debug-mainWindow"]/div/main/div[2]/div/div[2]',
    'modal_ok': '/html/body/div[7]/div/div/div[3]/a[2]',
    "datapacks_table": "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr",
    "dp_permalink": ".//a[@data-vrs-widget-field='getPermalink']",
    "dp_modal_close": "//a[@class='default-button text-button']",
    "files_table": "//li[@data-vrs-widget='LIWrapper']/div/div/form/div/a"
}

CSS = {
    "car_id": "p:nth-of-type(1)",
    "serie": 'td:nth-of-type(1) img',
    "serie_img": 'td:nth-of-type(1) img',
    "car_img": 'td:nth-of-type(2) img',
    "season": 'td:nth-of-type(3)',
    "author_img": 'td:nth-of-type(4) img',
    "dp_track": "td:nth-of-type(2) img",
    'dp_fastest_lap': "td:nth-of-type(3) div span:nth-of-type(1) span",
    'dp_time_of_day': "td:nth-of-type(4) div span:nth-of-type(1) span",
    'dp_track_state': "td:nth-of-type(4) div span:nth-of-type(2) span",
}


class wait_for_text_to_match(object):
    def __init__(self, locator, text):
        self.locator = text
        self.text = text

    def __call__(self, driver):
        try:
            element_text = EC._find_element(driver, self.locator).text
            return self.pattern.search(element_text)
        except StaleElementReferenceException:
            return False


def build_driver(browser="Chrome", headless=True, proxy=None):
    """
    Build a selenium driver for the desired browser with its parameters
    """
    # TODO Implement firefox, waiting for selenium 3.14.0 to fix timeout

    # Create needed directories if not existing
    for directory in needed_dirs:
        create_dirs(directory)

    # Set Chrome browser settings
    if browser == "Chrome":
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_arguments("--disable-dev-shm-usage"); // overcome limited resource problems
        options.add_arguments("--no-sandbox"); // Bypass OS security model
        options.add_experimental_option("prefs", {
            "download.default_directory": DL_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            'profile.default_content_setting_values.automatic_downloads': 1,
            "safebrowsing.enabled": False
        })

        if headless:
            options.add_argument('headless')
            # Not tested
            options.add_argument('disable-gpu')

        # TODO clean this
        
        # if os.name == 'posix':
        #     chromedriver = 'chromedriver_linux64'
        # elif os.name == 'nt':
        #     chromedriver = 'chromedriver_win32.exe'
#
        # if os.path.isfile(os.path.join(script_dir, chromedriver)):
        #     chromedriver_path = os.path.join(script_dir, chromedriver)
        # else:
        #     chromedriver_path = os.path.join(script_dir, 'scrapper', chromedriver)
#
        # if os.name == 'posix':
        #     os.chmod(chromedriver_path, 0o755)
#
        # print(os.path.join(script_dir, chromedriver_path))

        # Build Chrome driver
        driver = webdriver.Chrome(
            #executable_path=chromedriver_path,
            chrome_options=options)

        # Add devtools command to allow download
        driver.execute_cdp_cmd(
            'Page.setDownloadBehavior',
            {'behavior': 'allow', 'downloadPath': DL_DIR})

    elif browser == "Firefox":  # Handle Firefox profile

        # Build Firefox profile
        profile = webdriver.FirefoxProfile()
        profile.set_preference(
            'browser.download.folderList', 2,  # custom location
            'browser.download.manager.showWhenStarting', False,
            'browser.download.dir', DL_DIR,
            'browser.download.downloadDir', DL_DIR,
            'browser.helperApps.neverAsk.saveToDisk', 'application/zip',
            'browser.helperApps.neverAsk.saveToDisk',
            'application/octet-stream')

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
    """Wait for element to load by ID"""
    try:
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.ID, id)))
    except Exception:
        print(f"Unable to find element {id} in page")


def check_exists_by_xpath(driver, xpath):
    """Check if an element exists by its xpath"""
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def create_dirs(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def dl_img(url, dest=None):
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
    wait_by_xpath(driver, XPATH['cars_table'])

    # Retrieve cars table
    car_row = driver.find_elements_by_xpath(XPATH['cars_table'])

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
            CSS['car_id']
        ).get_attribute("innerHTML")

        soup = BeautifulSoup(node_span, "html.parser")
        for span in soup.findAll(
                "span", attrs={"data-vrs-widget-field": "packIdElement"}
        ):
            node_id = span.text

        # Create car dict
        car = {}
        car['serie'] = car_elem.find_element_by_css_selector(CSS['serie']).get_attribute('title')
        car['serie_img_url'] = car_elem.find_element_by_css_selector(CSS['serie_img']).get_attribute('src')
        car['serie_img_name'] = car['serie_img_url'].split('/')[-1]
        car['img_url'] = car_elem.find_element_by_css_selector(CSS['car_img']).get_attribute('src')
        car['img_name'] = car['img_url'].split('/')[-1]
        car['name'] = car_elem.find_element_by_css_selector(CSS['car_img']).get_attribute('title')
        car['season'] = car_elem.find_element_by_css_selector(CSS['season']).text
        car['author'] = car_elem.find_element_by_css_selector(CSS['author_img']).get_attribute('title')
        car['img_author'] = car_elem.find_element_by_css_selector(CSS['author_img']).get_attribute('src')
        car['id'] = node_id
        car['url'] = site_url + node_id
        car['premium'] = car_premium
        car['season_path'] = os.path.join(DL_DIR, car['season'])
        car['serie_path'] = os.path.join(
            car['season_path'].strip().replace(' ', '_'),
            car['serie'].strip().replace(' ', '_')
        )
        car['car_path'] = os.path.join(
            car['serie_path'].strip().replace(' ', '_'),
            car['name'].strip().replace(' ', '_')
        )

        cars.append(car)  # Add car to cars list

    return cars  # Return cars list


def authenticate(driver):
    """
    Authenticate using a Google account and return a boolean
    """

    print("Trying to authenticate")
    driver.get("https://virtualracingschool.appspot.com/#/Account/Billing")
    # Clic LOGIN Button
    wait_by_xpath(driver, XPATH['login_btn'])
    driver.find_element_by_xpath(XPATH['login_btn']).click()

    # click Login with google
    wait_by_xpath(driver, XPATH['ggl_login_btn'])
    driver.find_element_by_xpath(XPATH['ggl_login_btn']).click()

    # Accept ToS
    #try:
    #    wait_by_xpath(driver, '//input[@type="checkbox" and @value="on"]')
    #    driver.find_elements_by_xpath('//input[@type="checkbox" and @value="on"]')[0].click()  # Tick box
    #    driver.find_element_by_xpath('//a[text()="Confirm"]').click()
    #except Exception:
    #    pass

    # Type login
    wait_by_xpath(driver, XPATH['login_field'])
    driver.find_element_by_xpath(XPATH['login_field']).click()
    driver.find_element_by_xpath(XPATH['login_field']).send_keys(google_email)
    driver.find_element_by_xpath(XPATH['login_nxt']).click()

    # Type password
    wait_by_xpath(driver, XPATH['passwd_field'])
    time.sleep(3)
    driver.find_element_by_xpath(XPATH['passwd_field']).send_keys(google_password)
    time.sleep(5)  # crap wait do not remove (or fix it)
    driver.find_element_by_xpath(XPATH['passwd_nxt']).click()
    time.sleep(5)  # crap wait do not remove (or fix it)

    # Check if premium
    driver.get("https://virtualracingschool.appspot.com/#/Account/Settings")
    try:
        wait_by_xpath(driver, XPATH['subscr_div'])
        subscription_box = driver.find_element_by_xpath(XPATH['subscr_div'])  # Check if subscription box is displayed
    except StaleElementReferenceException:
        return False
    else:
        return subscription_box.is_displayed()
        #
        ## Accept ToS
        #try:
        #    wait_by_xpath(driver, '//input[@type="checkbox" and @value="on"]')
        #    driver.find_elements_by_xpath('//input[@type="checkbox" and @value="on"]')[0].click  # Tick box
        #    driver.find_element_by_xpath('//a[text()="Confirm"]').click
        #except Exception:
        #    pass
    #
        #return True
    #
    #except Exception:
    #    print('Failed to auth')
    #    return False


def build_files(driver, files_elem, dpack_path):
    files = []
    for elem in files_elem:
        file = {}
        file['name'] = re.sub("^.*\\\\", "", elem.get_attribute('text'))
        file["type"] = filetype.get(os.path.splitext(file['name'])[1][1:], "unknown")
        file['path'] = os.path.join(dpack_path, file['name'])

        filepath_temp = os.path.join(
            DL_DIR, file['name']
        )

        print(f"  |_ {file['name']}")

        # Download datapack file if not present
        if not os.path.isfile(file['path']) and "not uploaded" not in file['name']:
            #print(f"Downloading file {file['name']}")
            # Some files does not works VRS\18S4IMSA\W11-Daytona\VRS_18S4MB_RSR_Daytona_R2.sto
            try:
                elem.click()
            except Exception as e:
                print(f"Can't click: {file['name']}")
                traceback.print_stack()
                continue  # Go to next iteration if failed

            # Close modal License box if opened
            try:
                driver.find_element_by_xpath(XPATH['modal_ok']).click()
            except Exception as e:
                #print("Can't click: ", e)
                pass

            sleep_count = 0
            # Wait file to be downloaded (Chrome)
            while not (os.path.isfile(filepath_temp) and sleep_count < 180):
                # print('wait because part', sleep_count)
                time.sleep(1)
                sleep_count += 1

            print('-' * 12)
            print(f"Moving {filepath_temp} to {file['path']}")
            print('-' * 12)
            shutil.move(filepath_temp, file['path'])

        # Add file to files list
        files.append(file)

    return files


def build_datapacks_infos(driver, cars_list, premium=False):
    """
    Retrieve all available datapacks with infos and files
    """

    print("Building datapacks infos...")

    premium = authenticate(driver)
    #premium = False
    #print(f'Premium: {premium}' )

    # Temp crap due tu aussie driver search
    cars_list = [item for item in cars_list if item['serie'] != "Aussie Driver Search"]

    if not premium:  # Define list to iterate over
        cars_list = [item for item in cars_list if not item['premium']]

    for car in cars_list:  # Build datapacks

        car['datapacks'] = []  # Initialize datapacks list
        print(f"|_ Building {car['serie']} - {car['name']} datapacks")

        driver.get(car['url'])  # Load car URL and wait Js load
        #TODO doesn't works due to text() usage
        # TEST
        time.sleep(3)
        WebDriverWait(driver, 10).until(wait_for_text_to_match((By.XPATH, "//p[@class='base-info']"), f"{car['name']}"))
        #wait_by_xpath(
        #    driver,
        #    f"//p[@class='base-info' and text()=\'{car['name']}\']")

        # Iterate over DataPacks tables TR
        # car_elems = iter_dom(driver, XPATH['datapacks_table'])
        # for car_elem in car_elems:

        # Build datapacks infos
        for car_elem in iter_dom(driver, XPATH['datapacks_table']):
            # Skip "previous week"
            if car_elem.find_element_by_css_selector("a").get_attribute('text') == "Show previous weeks":
                continue

            datapack = {}  # Create datapack dict

            try:  # Build datapack
                datapack['track'] = car_elem.find_elements_by_css_selector(
                    CSS['dp_track'])[0].get_attribute('title')
                datapack['fastest_laptime'] = car_elem.find_elements_by_css_selector(
                    CSS['dp_fastest_lap'])[0].get_attribute('title')
                datapack['time_of_day'] = car_elem.find_elements_by_css_selector(
                    CSS['dp_time_of_day'])[0].get_attribute('title')
                datapack['track_state'] = car_elem.find_elements_by_css_selector(
                    CSS['dp_track_state'])[0].get_attribute('title')

                print(f" |_ {datapack['track']}")

                # If datapack is not empty
                if datapack['fastest_laptime'] != "":
                    car_elem.find_element_by_xpath(XPATH["dp_permalink"]).click()
                    time.sleep(1)

                    # Get datapack permalink
                    datapack['url'] = driver.find_element_by_css_selector(
                        ".gwt-TextBox"
                    ).get_attribute('value')

                    # Close modal
                    time.sleep(1)
                    driver.find_element_by_xpath(XPATH['dp_modal_close']).click()
                    time.sleep(1)
                car['datapacks'].append(datapack)

            except Exception as e:
                driver.save_screenshot('screen.png')
                print('ERR', e)
                traceback.print_stack()
                print(datapack)
                # pass

        # Retrieve datapacks files
        datapack_path = ''
        for datapack in car['datapacks']:
            #print(json.dumps(datapack, indent=4))
            #print(f" |_ {datapack['track']}")
            datapack['files'] = []

            datapack_path = os.path.join(  # Build desired paths
                car['car_path'], datapack['track'])
            create_dirs(datapack_path)  # Create paths if needed

            if "url" in datapack:  # If datapack has url
                driver.get(datapack['url'])  # Load datapack url
                #print('-' * 12)
                #print(datapack['url'])
                #print('-' * 12)

                # TODO This seems really slow, potentially not working
                time.sleep(3)
                wait_by_xpath(driver, f"//span[text()='{datapack['track']}']")  # Wait page

                # Iterate over files
                file_elements = iter_dom(driver, XPATH['files_table'])

                # Remove not uploaded files (GG VRS)
                file_elements = [item for item in file_elements if "not uploaded" not in item.get_attribute('text')]
                cars_list = [item for item in cars_list if item['serie'] != "Aussie Driver Search"]

                # Download Car image
                if not os.path.exists(os.path.join(car['car_path'], "logo.jpg")):
                    print('-' * 12)
                    print(f"DL {car['img_url']} to {car['car_path']}")
                    dl_img(car['img_url'], os.path.join(car['car_path'], f"logo{os.path.splitext(car['img_url'])[1]}"))
                # Download Serie image
                if not os.path.exists(os.path.join(car['serie_path'], "logo.jpg")):
                    print('-' * 12)
                    print(f"DL {car['serie_img_url']} to {os.path.join(car['serie_path'], 'logo.jpg')}")
                    dl_img(car['serie_img_url'], os.path.join(car['serie_path'], f"logo{os.path.splitext(car['serie_img_url'])[1]}"))

                datapack['files'] = build_files(driver, file_elements, datapack_path)


    #print(cars_list)

    # pickle.dump(cars_list, open(settings.history_file,'wb'))

    with open(os.path.join(DL_DIR, 'data.json'), 'w') as tempfile:
        json.dump(cars_list, tempfile)

    driver.close()

    return cars_list


if __name__ == '__main__':

    driver = build_driver(headless=False)
    cars_list = build_cars_list(driver)  # Create cars list
    print(json.dumps(cars_list, indent=4))
    build_datapacks_infos(driver, cars_list)  # Build cars datapacks

    # with open ('data.json', 'w') as tempfile:
    #    json.dump(cars_list, tempfile)

    # print(json.dumps(cars_list, indent=4))

    # Finaly close the browser
    # driver.close()
