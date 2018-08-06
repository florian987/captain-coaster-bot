# -*- coding: utf-8 -*-

import os
import time
import json
import traceback
import shutil
import urllib
import pickle

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException      
from selenium.webdriver.chrome.options import Options

try:
    import settings
except ModuleNotFoundError:
    import cogs.scrapper.settings as settings
except:
    print("Can not load settings")

script_dir = os.path.dirname(os.path.realpath(__file__))
download_dir = os.path.join(script_dir, "downloads")
log_dir = os.path.join(script_dir, "logs")
gecko_log_path = os.path.join(log_dir, "geckodriver.log")


needed_dirs = [
    download_dir,
    log_dir
]


def build_driver(browser="Chrome", headless=True, proxy=None):



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

            #download_path = download_dir

        # Build Chrome driver
        driver = webdriver.Chrome(chrome_options=options)

        # Add devtools command to allow download
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': download_dir})

    # Handle Firefox profile
    elif browser == "Firefox":

        # Build Firefox profile
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2) # custom location
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.download.dir', download_dir)
        profile.set_preference('browser.download.downloadDir', download_dir)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk','application/zip')
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk','application/octet-stream')

        # Proxy settings
        if proxy:
            firefox_proxy = Proxy({
                'proxyType': ProxyType.MANUAL,
                'httpProxy': settings.PROXY,
                'ftpProxy': settings.PROXY,
                'sslProxy': settings.PROXY,
                'noProxy': '' # set this value as desired
            })

            driver = webdriver.Firefox(profile, proxy=firefox_proxy, log_path=gecko_log_path) # Ajout du proxy

        else:
            # Build Firefox driver without proxy
            driver = webdriver.Firefox(profile, log_path=gecko_log_path) # Ajout du proxy

    # Set global driver settings
    #driver.implicitly_wait(60)
    driver.set_page_load_timeout(90)

    return driver

        


def iter_dom(driver, xpath):
    def get_next_element(elems, idx):
      for i, element in enumerate(elems):
         #print("get elem : %s / %s / %s" % (i, idx, element))
        if i == idx:
            return element
    
    current_idx = 0
    has_elements = True
    while has_elements:
        elements = driver.find_elements_by_xpath(xpath)
        #print(driver.current_url)
        try:
            elem = get_next_element(elements, current_idx)
            #print("Try1: %s / %s" % (current_idx, elem))
            if elem:
                yield elem
        except Exception as e:
            elements = driver.find_elements_by_xpath(xpath)
            elem = get_next_element(elements, current_idx)
            #print("Try2: %s / %s / %s" % (current_idx, elem, e))
            if elem:
                yield elem

        if elem:
            current_idx += 1
        else:
            has_elements = False 




def wait_by_xpath(driver, xpath, retries=20):
    """Wait for xpath element to load"""
    try:
        element = WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
    except:
        print("Unable to find element {} in page".format(xpath))

def wait_by_css(driver, css, retries=20):
    """Wait for css element to load"""
    try:
        element = WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css)))
    except:
        print("Unable to find element {} in page".format(css))

def wait_by_id(driver, id, retries=20):
    """Wait for element to load by ID"""
    try:
        element = WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.ID, id)))
    except:
        print("Unable to find element {} in page".format(id))





def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def create_dirs(directory):
    if not os.path.exists(directory):
        #print("|__ Creating unexisting directory: " + directory)
        os.makedirs(directory)

def download_img(url, dest=None):
    # Set filename from url
    url_filename = url.split('/')[-1]

    if dest is None:
        urllib.request.urlretrieve(url, url_filename)
    else:
        # If filename not in dest
        if not "." in dest.split('/')[-1]:
            file_dest = os.path.join(dest, url_filename)

        # If filename in dest    
        else:
            file_dest = dest

        # Download if not exists    
        if not os.path.isfile(file_dest):
            urllib.request.urlretrieve(url, file_dest)



def build_cars_list(driver):
    """Build cars list from datapacks page"""

    print("- Retrieving cars list ...")
    driver.get("https://virtualracingschool.appspot.com/#/DataPacks")

    # Wait JavaScript to load cars table
    wait_by_xpath(driver, "//table[@data-vrs-widget='tableWrapper']/tbody/tr")

    # Retrieve cars table
    car_row = driver.find_elements_by_xpath("//table[@data-vrs-widget='tableWrapper']/tbody/tr")

    # Initialize cars array
    cars = []

    # Iterate over table car_elements
    for car_element in car_row:
        
        # Set premium status depending of style display
        if "visible" in car_element.find_element_by_class_name('blue').get_attribute('style'):
            car_premium = True
        else:
            car_premium = False

        # Get car ID
        node_span = car_element.find_element_by_css_selector("p:nth-of-type(1)").get_attribute("innerHTML")
        soup = BeautifulSoup(node_span, "html.parser")
        for span in soup.findAll("span", attrs={"data-vrs-widget-field":"packIdElement"}):
            node_id = span.text

        # Create car dict
        car = {}
        car['serie'] = car_element.find_element_by_css_selector('td:nth-of-type(1) img').get_attribute('title')
        car['serie_img_url'] = car_element.find_element_by_css_selector('td:nth-of-type(1) img').get_attribute('src')
        car['serie_img_name'] = car['serie_img_url'].split('/')[-1]
        car['img_url'] = car_element.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('src')
        car['img_name'] = car['img_url'].split('/')[-1]
        car['name'] = car_element.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('title')
        car['season'] = car_element.find_element_by_css_selector('td:nth-of-type(3)').text
        car['author'] = car_element.find_element_by_css_selector('td:nth-of-type(4) img').get_attribute('title')
        car['img_author'] = car_element.find_element_by_css_selector('td:nth-of-type(4) img').get_attribute('src')
        car['id'] = node_id
        car['url'] = "https://virtualracingschool.appspot.com/#/DataPacks/" + node_id
        car['premium'] = car_premium
        car['season_path'] = os.path.join(download_dir, car['season'])
        car['serie_path'] = os.path.join(car['season_path'], car['serie'])
        car['car_path'] = os.path.join(car['serie_path'], car['name'])

        # Add car to cars list
        cars.append(car)

    # Return cars list
    return cars
    







def build_datapacks_infos(driver, cars_list, premium=False):
    
   # # Auth
   # wait_by_xpath(driver, "//span[text()='Login / Logout']]")
   # driver.find_element_by_xpath("//a[@data-vrs-widget='MenuLink'][4]").click()
#
   # wait_by_id(driver, By.ID, "gwt-debug-googleLogin")
   # driver.find_element_by_id("gwt-debug-googleLogin").click
#
   # try:
   #     wait_by_css(driver, "//a[@class='KM1CN4-a-v']", 5)
   #     driver.find_element_by_class_name('KM1CN4-a-v').click
   # except:
   #     pass
   # 
#
#
    # Define list to iterate over
    if not premium:
        cars_list = [item for item in cars_list if not item['premium']]
    

    # Build datapacks
    for car in cars_list:

        # Initialize datapacks list
        car['datapacks'] = []

        # Only iterate over free cars
        if car['premium'] == False:
            
            print("|_ Building {} - {} datapacks".format(car['serie'], car['name']))
            
            # Load car URL and wait Js load
            driver.get(car['url'])
            wait_by_xpath(driver, "//p[@class='base-info' and text()=\"" + car['name'] +"\"]")

            # Iterate over DataPacks tables TR
            car_elements = iter_dom(driver, "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")
            for car_element in car_elements:

                # Create datapacks list
                datapack = {}

                datapack_path = ''

                # Build datapack
                try:

                    datapack['track'] = car_element.find_elements_by_css_selector(
                        "td:nth-of-type(2) img"
                        )[0].get_attribute('title')

                    datapack['fastest_laptime'] = car_element.find_elements_by_css_selector(
                        "td:nth-of-type(3) div span:nth-of-type(1) span"
                        )[0].get_attribute('title')

                    datapack['time_of_day'] = car_element.find_elements_by_css_selector(
                        "td:nth-of-type(4) div span:nth-of-type(1) span"
                        )[0].get_attribute('title')
                        
                    datapack['track_state'] = car_element.find_elements_by_css_selector(
                        "td:nth-of-type(4) div span:nth-of-type(2) span"
                        )[0].get_attribute('title')

                    # If datapack is not empty
                    if datapack['fastest_laptime'] != "":  

                        # Open permalink box
                        car_element.find_element_by_css_selector(
                            "td:nth-of-type(6) a:nth-of-type(3)").click()

                        # Get datapack permalink
                        datapack['url'] = driver.find_element_by_css_selector(
                            ".gwt-TextBox").get_attribute('value')

                        # Close modal
                        driver.find_element_by_css_selector(
                                ".KM1CN4-a-h a").click()

                    car['datapacks'].append(datapack)

                except Exception as e:
                    #print('ERR', e)
                    #traceback.print_stack()
                    pass


            for datapack in car['datapacks']:
                datapack['files'] = []

                # Build desired paths
                datapack_path = os.path.join(car['car_path'], datapack['track'])                        
                # Create paths if needed
                create_dirs(datapack_path)

                # Load car URL and wait Js load
                if "url" in datapack:
                    
                    # Load datapack url
                    driver.get(datapack['url'])
                    
                    # Wait page to be loaded
                    wait_by_xpath(driver, "//span[text()=\"" + datapack['track'] +"\"]")
                    #print('page: ' + driver.current_url)

                    # Iterate over files
                    file_elements = iter_dom(driver, "//li[@data-vrs-widget='LIWrapper']/div/div/form/div/a")
                    for file_element in file_elements:
                       
                        # Define extensions dict
                        filetype = {
                            "olap": "hotlap",
                            "blap": "bestlap",
                            "rpy": "replay",
                            "zip": "replay",
                            "sto": "setup"
                        }
                        
                        # Create file dict
                        file = {}

                        # Set filename
                        file['name'] = file_element.get_attribute('text')

                        # Set filetype
                        file_extension = file['name'].split('.')[-1]
                        file["type"] = filetype.get(file_extension, "unknown")
#
                        filepath_temp = os.path.join(download_dir, file['name'])
                        file['path'] = os.path.join(datapack_path, file['name'])

                        # Download Car image if needed
                        download_img(car['img_url'], car['car_path'])

                        # Download Serie image if needed
                        download_img(car['serie_img_url'], car['serie_path'])
                    
                        # Download datapack file if not present
                        if not os.path.isfile(file['path']):
                            #time.sleep(1)
                            try:
                                file_element.click()
                            except:
                                print("Can not click")
                            #time.sleep(1)

                            # Close modal License box if opened
                            try:
                                ok_button = driver.find_element_by_xpath('/html/body/div[7]/div/div/div[3]/a[2]')
                                ok_button.click()
                                #time.sleep(1)
                            except Exception as e:
                                pass

                            sleep_count = 0
                            # Wait file to be downloaded (Chrome)
                            while not os.path.isfile(filepath_temp) and sleep_count < 180:
                                #print('wait because part', sleep_count)
                                time.sleep(1)
                                sleep_count += 1

                            shutil.move(filepath_temp, file['path'])
                            
                            # Wait file to be downloaded (Firefox)
                            #sleep_count = 0
                            #while os.path.isfile(filepath_temp + '.part') and sleep_count < 90:
                            #    print('wait because part', sleep_count)
                            #    time.sleep(1)
                            #    sleep_count += 1

                            #print('download OK', 'Temp_path: ' + filepath_temp)

                            # Move file
                            #if not os.path.isfile(filepath_temp + '.part') and os.path.isfile(filepath_temp):
                            #    shutil.move(filepath_temp, file['path'])
                            #
                            #    #time.sleep(5)
                            
                        # Add file to datapck list
                        datapack['files'].append(file)
            
    #pickle.dump(cars_list, open(settings.history_file,'wb'))

    with open (os.path.join(download_dir,'data.json'), 'w') as tempfile:
        json.dump(cars_list, tempfile)

    driver.close()
    
    return cars_list


if __name__ == '__main__':

    driver = build_driver()
    # Create cars list
    cars_list = build_cars_list(driver)
    # Build cars datapacks
    build_datapacks_infos(driver, cars_list)

    #with open ('data.json', 'w') as tempfile:
    #    json.dump(cars_list, tempfile)

    #print(json.dumps(cars_list, indent=4))


    # Finaly close the browser
    driver.close()


