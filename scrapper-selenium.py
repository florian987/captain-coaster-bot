# -*- coding: utf-8 -*-

import os
import time
import json
import traceback

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException        

# Settings
PROXY = "fw_in.bnf.fr:8080"
script_dir = os.path.dirname(os.path.realpath(__file__))
download_dir = script_dir + "/downloads"

print(download_dir)

proxy = Proxy({
    'proxyType': ProxyType.MANUAL,
    'httpProxy': PROXY,
    'ftpProxy': PROXY,
    'sslProxy': PROXY,
    'noProxy': '' # set this value as desired
    })

profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', download_dir)
profile.set_preference('browser.download.downloadDir', download_dir)
profile.set_preference('browser.helperApps.neverAsk.saveToDisk','application/zip')
profile.set_preference('browser.helperApps.neverAsk.saveToDisk','application/octet-stream')



# Initialize selenium driver
#driver = webdriver.Firefox(profile)
driver = webdriver.Firefox(profile, proxy=proxy) # Ajout du proxy

#driver.add_cookie({"host":"virtualracingschool.appspot.com","domain":"virtualracingschool.appspot.com","secure":False,"expire":1533023830,"name":"vrs","value":"zkXqnElNVioRWuUK1JgojA"})




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




def wait_by_xpath(xpath, retries=20):
    """Wait for xpath element to load"""
    try:
        element = WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
    except:
        print("Unable to find element {} in page".format(xpath))

def wait_by_css(css, retries=20):
    """Wait for css element to load"""
    try:
        element = WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css)))
    except:
        print("Unable to find element {} in page".format(css))





def check_exists_by_xpath(xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True



def build_cars_list():
    """Build cars list from datapacks page"""

    print("-- Gathering cars ...")

    driver.get("https://virtualracingschool.appspot.com/#/DataPacks")

    # Wait JavaScript to load cars table
    wait_by_xpath("//table[@data-vrs-widget='tableWrapper']/tbody/tr")

    # Retrieve cars table
    car_row = driver.find_elements_by_xpath("//table[@data-vrs-widget='tableWrapper']/tbody/tr")



    # Initialize cars array
    iracing_cars = []

    # Iterate over table car_elements
    for car_element in car_row:
        
        # Retrieve cars infos
        car_serie = car_element.find_element_by_css_selector('td:nth-of-type(1) img').get_attribute('title')
        car_name = car_element.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('title')
        car_season = car_element.find_element_by_css_selector('td:nth-of-type(3)').text
        car_author = car_element.find_element_by_css_selector('td:nth-of-type(4) img').get_attribute('title')
        #print(serie_node)

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

        #iracing_series.append(serie_node)

        # Create car dict
        car = {}
        car['serie'] = car_serie
        car['name'] = car_name
        car['season'] = car_season
        car['author'] = car_author
        car['id'] = node_id
        car['url'] = "https://virtualracingschool.appspot.com/#/DataPacks/" + node_id
        car['premium'] = car_premium

        iracing_cars.append(car)

        #print(json.dumps(car, indent=4))


    # debug cars list
    #print(json.dumps(iracing_cars, indent=4))

    # Return cars list
    return iracing_cars
    







def build_datapacks_infos(cars_list):
    for car in cars_list:

        # Initialize datapacks list
        car['datapacks'] = []

        # Only iterate over free cars
        if car['premium'] == False:
            
            print("|_ Building {} datapacks".format(car['name']))
            
            # Load car URL and wait Js load
            driver.get(car['url'])
            wait_by_xpath("//p[@class='base-info' and text()=\"" + car['name'] +"\"]")

            # Iterate over DataPacks tables TR
            car_elements = iter_dom(driver, "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")
            for car_element in car_elements:

                # Create datapacks list
                datapack = {}

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

                    if datapack['fastest_laptime'] != "":
                        car_element.find_element_by_css_selector(
                        "td:nth-of-type(6) a:nth-of-type(3)"
                        ).click()

                        datapack['url'] = driver.find_element_by_css_selector(
                            ".gwt-TextBox"
                            ).get_attribute('value')

                        # Close modal
                        driver.find_element_by_css_selector(
                                ".KM1CN4-a-h a"
                                ).click()

                    print(datapack)

                    car['datapacks'].append(datapack)

                except Exception as e:
                    #print('ERR', e)
                    #traceback.print_stack()
                    continue


            for datapack in car['datapacks']:
                datapack['files'] = []
                
                # Load car URL and wait Js load
                if "url" in datapack:
                    print('-' * 22)
                    driver.get(datapack['url'])
                    #wait_by_xpath("//li[@data-vrs-widget='LIWrapper']")
                    print('before')
                    # TODO Fix XPATH
                    wait_by_xpath("/html/body/div[1]/div/div/main/div[2]/div/div[3]/div/div/div/div/div/div[2]/div[1]/div[1]/div/div/ul/li[1]/div/div/form/div/a")
                    #wait_by_css("li[data-vrs-widget=LIWrapper]")
                    print('after')

                    #time.sleep(3)

                    #for datapack_line in driver.find_elements_by_class_name('session-file'):
                        
                        #print(dir(datapack_line))
                        #file_elements = datapack_line.find_elements_by_class_name('gwt-Anchor')
                    file_elements = iter_dom(driver, "//li[@data-vrs-widget='LIWrapper']/div/div/form/div/a")
                    for file_element in file_elements:
                        file = {}

                        file['name'] = file_element.get_attribute('text')

                        # Set filetype
                        file_extension = file['name'].split('.')[-1]
                        if file_extension == "olap":
                            file['type'] = "hotlap"
                        elif file_extension == "blap":
                            file['type'] = "bestlap"
                        elif file_extension == "rpy":
                            file['type'] = "replay"
                        elif file_extension == "sto":
                            file['type'] = "setup"
                        else:
                            file['type'] = "unknown"


                        datapack['files'].append(file)
                    
                        # Download file if not there
                        print(os.path.isfile(os.path.join(download_dir, file['name'])))
                        print(os.path.join(download_dir, file['name']))
                        if not os.path.isfile(os.path.join(download_dir, file['name'])):
                            print('before click')
                            time.sleep(4)
                            file_element.click()
                            print('after click')
                            time.sleep(4)

                            try:
                                #wait_by_css(".KM1CN4-a-k", 3)
                                #driver.find_element_by_xpath('/html/body/div[7]/div/div/div[3]/a[2]').click()
                                ok_button = driver.find_element_by_xpath('/html/body/div[7]/div/div/div[3]/a[2]')
                                ok_button.click()
                                #print(ok_button.get_attribute('innerHTML'))
                                time.sleep(4)
                            #except selenium.common.exceptions.ElementClickInterecptedException as e:
                            #    print(e)
                            except Exception as e:
                            #    driver.find_element_by_css_selector('.KM1CN4-a-h a:nth-of-type(2)').click
                                print('ERR', e)
                            #    #continue
    #
                                #time.sleep(5)
                            

            
            #print(json.dumps(car, indent=4))
    return cars_list


# Create cars list
cars_list = build_cars_list()

# Build cars datapacks
build_datapacks_infos(cars_list)

#with open ('data.json', 'w') as tempfile:
#    json.dump(cars_list, tempfile)

#print(json.dumps(cars_list, indent=4))


# Finaly close the browser
driver.close()


