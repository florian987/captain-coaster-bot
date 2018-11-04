# -*- coding: utf-8 -*-

# import pickle
import traceback
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

google_email = "osmozwareesport@gmail.com"
google_password = "Nj689933"
google_cookie = {
    'domain': 'virtualracingschool.appspot.com',
    'expiry': 1542534627,
    'httpOnly': False,
    'name': 'JSESSIONID',
    'path': '/',
    'secure': False,
    'value': 'LCT1XmGyJ_4-ZZvX-eALuA'
    }

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
        options.add_experimental_option("prefs", {
            "download.default_directory": DL_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        })

        if headless:
            options.add_argument('headless')
            # Not tested
            options.add_argument('disable-gpu')

        # TODO clean this
        if os.name == 'posix':
            chromedriver = 'chromedriver_linux64'
        elif os.name == 'nt':
            chromedriver = 'chromedriver_win32.exe'

        if os.path.isfile(os.path.join(script_dir, chromedriver)):
            chromedriver_path = os.path.join(script_dir, chromedriver)
        else:
            chromedriver_path = os.path.join(script_dir, 'scrapper', chromedriver)

        print(os.path.join(script_dir, chromedriver_path))

        # Build Chrome driver
        driver = webdriver.Chrome(
            executable_path=chromedriver_path,
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
        car['season_path'] = os.path.join(DL_DIR, car['season'])
        car['serie_path'] = os.path.join(car['season_path'], car['serie'])
        car['car_path'] = os.path.join(car['serie_path'], car['name'])

        cars.append(car)  # Add car to cars list

    return cars  # Return cars list


def authenticate(driver):
    """
    Authenticate using a Google account and return a boolean
    """

    print("Trying to authenticate")
    
    # driver.get("https://virtualracingschool.appspot.com/#/DataPacks")
    driver.get("https://virtualracingschool.appspot.com/#/Account/Billing")
    driver.add_cookie(google_cookie)

    #try:
        # Open menu
        # wait_by_xpath(driver, "//a[@data-activates='sidenavCollapse']")
        # driver.find_element_by_xpath("//a[@data-activates='sidenavCollapse']").click()

        # Derouler menu
        # driver.find_element_by_css_selector(
        #     'i.material-icons:nth-child(4)'
        # driver.find_element_by_xpath(
        #     '//*[@id="sidenavCollapse"]/ul/li[1]/div[1]/a'
        # ).click

        # Click login button
        # wait_by_xpath(driver, '//*[@id="sidenavCollapse"]/ul/li[1]/div[2]/ul/li[5]/a')
        # driver.find_element_by_xpath(
        #     '//*[@id="sidenavCollapse"]/ul/li[1]/div[2]/ul/li[5]/a'
        # ).click
        #wait_by_xpath(driver, '//*[@id="gwt-debug-mainWindow"]/div/main/div[2]/div/div/div[2]/a/span')
        #driver.find_element_by_xpath(
        #    '//*[@id="gwt-debug-mainWindow"]/div/main/div[2]/div/div/div[2]/a/span'
        #).click()
#
        #print(driver.find_element_by_class_name('popupContent').get_attribute('innerHTML'))
#
        ## click Login with google
        #wait_by_xpath(driver, '//*[@id="gwt-debug-googleLogin"]')
        #driver.find_element_by_xpath('//*[@id="gwt-debug-googleLogin"]').click()
#
        ## Accept ToS
        #try:
        #    wait_by_xpath(driver, '//input[@type="checkbox" and @value="on"]')
        #    driver.find_elements_by_xpath('//input[@type="checkbox" and @value="on"]')[0].click()  # Tick box
        #    driver.find_element_by_xpath('//a[text()="Confirm"]').click()
        #except Exception:
        #    pass
#
        ## Type login
        #wait_by_xpath(driver, '//input[@type="email"]')
        #driver.find_element_by_xpath('//input[@type="email"]').click()
        #driver.find_element_by_xpath('//input[@type="email"]').send_keys(google_email)
        #driver.find_element_by_css_selector(
        #    '#identifierNext > div:nth-child(2)'
        #).click()
#
        ## Type password
        #wait_by_xpath(driver, "//input[@type='password']")
        #driver.find_element_by_xpath("//input[@type='password']").send_keys(google_password)
        #driver.find_element_by_css_selector(
        #    '#passwordNext > div:nth-child(2)'
        #).click()
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
        #return False


def build_datapacks_infos(driver, cars_list, premium=False):
    """
    Retrieve all available datapacks with infos and files
    """

    print("Building datapacks infos...")

    premium = authenticate(driver)

    if not premium:  # Define list to iterate over
        cars_list = [item for item in cars_list if not item['premium']]

    for car in cars_list:  # Build datapacks

        car['datapacks'] = []  # Initialize datapacks list
        print(f"|_ Building {car['serie']} - {car['name']} datapacks")

        driver.get(car['url'])  # Load car URL and wait Js load
        wait_by_xpath(
            driver,
            "//p[@class='base-info' and text()=\"{car['name']}\"]")

        # Iterate over DataPacks tables TR
        car_elems = iter_dom(driver, "//table[@data-vrs-widget="
                                "'DataPackWeeksTable']/tbody/tr")

        for car_elem in car_elems:
            # Skip "previous week"
            if car_elem.find_element_by_css_selector("a").get_attribute('text') == "Show previous weeks":
                continue

            datapack = {}  # Create datapack dict
            datapack_path = ''

            try:  # Build datapack
                #print(car_elem.find_element_by_css_selector("a").get_attribute('text'))
                #print(car_elem.find_element_by_xpath("//td[@class='thumbnail-column']/div/img").get_attribute("title"))
                #datapack['track'] = car_elem.find_elements_by_xpath("//td[@class='thumbnail-column'/img").get_attribute("title")

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
                    #car_elem.find_element_by_css_selector(
                    car_elem.find_element_by_xpath(
                        #"td:nth-of-type(6) a:nth-of-type(3)"
                        "//a[@data-vrs-widget-field='getPermalink']"
                    ).click()

                    # Get datapack permalink
                    datapack['url'] = driver.find_element_by_css_selector(
                        ".gwt-TextBox"
                    ).get_attribute('value')

                    # Close modal
                    driver.find_element_by_xpath(
                        "//a[@class='default-button text-button']"
                    ).click()

                car['datapacks'].append(datapack)

            except Exception as e:
                driver.save_screenshot('screen.png')
                print('ERR', e)
                traceback.print_stack()
                print(datapack)
                # pass

        for datapack in car['datapacks']:
            datapack['files'] = []

            datapack_path = os.path.join(  # Build desired paths
                car['car_path'], datapack['track'])

            create_dirs(datapack_path)  # Create paths if needed

            if "url" in datapack:  # If datapack has url

                driver.get(datapack['url'])  # Load datapack url
                wait_by_xpath(driver, f"//span[text()='{datapack['track']}']")  # Wait page
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
                        DL_DIR, file['name']
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
                        print(f"Downloading file {file['name']}")
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
                        while not (os.path.isfile(filepath_temp) and sleep_count < 180):
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

    print(cars_list)

    # pickle.dump(cars_list, open(settings.history_file,'wb'))

    with open(os.path.join(DL_DIR, 'data.json'), 'w') as tempfile:
        json.dump(cars_list, tempfile)

    driver.close()

    return cars_list


if __name__ == '__main__':

    driver = build_driver(headless=False)
    cars_list = build_cars_list(driver)  # Create cars list
    build_datapacks_infos(driver, cars_list)  # Build cars datapacks

    # with open ('data.json', 'w') as tempfile:
    #    json.dump(cars_list, tempfile)

    # print(json.dumps(cars_list, indent=4))

    # Finaly close the browser
    # driver.close()
