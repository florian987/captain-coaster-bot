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

# Proxy Settings
PROXY = "fw_in.bnf.fr:8080"

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
profile.set_preference('browser.download.dir', './downloads/')
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
            #for car_element in iter_dom(driver, "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[@class='KM1CN4-W-f']"):
            car_elements = iter_dom(driver, "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")
            for car_element in car_elements:

                # Create datapacks list
                datapack = {}

                # Build datapack
                try:
                    #print(car_element.get_attribute('innerHTML'))

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

                    for datapack_line in driver.find_elements_by_class_name('session-file'):
                        print('inline')
                        
                        #print(dir(datapack_line))
                        file_elements = datapack_line.find_elements_by_class_name('gwt-Anchor')
                        for file_element in file_elements:
                            file = {}
                            
                            #print(dir(file_element))
                            #print(file_element.get_attribute('innerHTML'))
                            #print(file_element.get_attribute('text'))

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
                        
                            time.sleep(5)
                            #file_element.click()

                            try:
                                file_element.click()
                                #wait_by_css(".KM1CN4-a-i", 3)
                                #wait_by_css(".KM1CN4-a-k", 3)
                            #    wait_by_xpath(".KM1CN4-a-k", 3)
                            #    driver.find_element_by_css_selector('.KM1CN4-a-h a:nth-of-type(2)').click
                            #except selenium.common.exceptions.ElementClickInterecptedException as e:
                            #    print(e)
                            except Exception as e:
                                driver.find_element_by_css_selector('.KM1CN4-a-h a:nth-of-type(2)').click
                                print('ERR', e)
                                #continue

                            time.sleep(5)
                                

                #    # Load datapack page
                #    car_element.find_element_by_css_selector("td:nth-of-type(7) a").click()
                #    # Wait page load
                #    wait_by_xpath("//div[@data-vrs-widget='ListView']/ul")
#
                #    datapack['files'] = []
                #    for line in driver.find_elements_by_css_selector("form.session-file-name"):
                #        print(line.get_attribute('innerHTML'))
            #            for file in line.find_elements_by_css_selector("a.gwt-Anchor"):
#
            #                # Download file
            #                file.click
            #                # Try block to catch download popup
            #                try:
            #                    driver.find_element_by_xpath("/html/body/div[7]/div/div/div[3]/a[2]").click
            #                except:
            #                    continue
            #                
#
            #                # Build filename_list
            #                filename = str(file.text).replace(' .','.').replace(' ','_')
#
            #                print(filename)
#
            #                # Add filename to list
            #                datapack_file = {}
            #                datapack_file['name'] = filename
#
            #                # Set filetype
            #                file_extension = filename.split('.')[-1]
            #                if file_extension == "olap":
            #                    datapack_file['type'] = "hotlap"
            #                elif file_extension == "blap":
            #                    datapack_file['type'] = "bestlap"
            #                elif file_extension == "rpy":
            #                    datapack_file['type'] = "replay"
            #                elif file_extension == "sto":
            #                    datapack_file['type'] = "setup"
            #                else:
            #                    datapack_file['type'] = "unknown"
#
#
            #                # Append file to datapac
            #                datapack['files'].append(datapack_file)
            #        
            #        driver.back()
            #        time.sleep(3)
                

                    
                    
                    #print(datapack_files)

                #row_count += 1

                # GoTo DataPack Page
                # if datapck not empty ?
                #goto_datapack = car_element.find_element_by_css_selector('td:nth-of-type(7) a').click()
    #
                #goto_datapack
    #
                #time.sleep(3)
    #
                #session_files = driver.find_elements_by_css_selector("div.vrs-list-view")
                #print(len(session_files))
                #print(session_files)
                #for session_row in session_files:
                #    print(dir(session_row.find_elements_by_css_selector("form.session-file-name div a ")))
                #    #file_name = session_row.find_elements_by_css_selector("form.session-file-name div a ").text
                #    #file_grab = session_row.find_elements_by_css_selector("form.session-file-name div a").click()
    ##
                #    #print(file_name)
                #    
        #        driver.back()
        #        time.sleep(3)
                

            #goto_datapack = car_element.find_element_by_css_selector('td:nth-of-type(7) a').click()


            #datapack['track'] = car_element.find_element_by_xpath("//td[2]/div/span[1]").get_attribute("innerHTML")

            #laptime_span = car_element.find_element_by_css_selector("td:nth-of-type(3)").get_attribute("innerHTML")
            #soup = BeautifulSoup(node_span, "html.parser")
            #for span in soup.findAll("span", attrs={"data-vrs-widget-field":"packIdElement"}):
            #    node_id = span.text
            # lap-time-widget

            
            
            #print(json.dumps(car, indent=4))
    return cars_list

#def get_datapacks_files(cars_list):
    

# Create cars list
cars_list = build_cars_list()

# Build cars datapacks
build_datapacks_infos(cars_list)

#with open ('data.json', 'w') as tempfile:
#    json.dump(cars_list, tempfile)

#print(json.dumps(cars_list, indent=4))


# Finaly close the browser
driver.close()


