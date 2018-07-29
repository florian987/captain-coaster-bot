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
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/zip')



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


def check_exists_by_xpath(xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True



def build_cars_list():
    """Build cars list from datapacks page"""

    print("Start cars list building ...")

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
        car_car = car_element.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('title')
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
        car['car'] = car_car
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
    


# Create cars list
cars_list = build_cars_list()




def build_datapacks_infos(cars_list):
    for car in cars_list:

        # Initialize datapacks list
        car['datapacks'] = []

        # Only iterate over free cars
        if car['premium'] == False:
            
            # Load car URL and wait Js load
            driver.get(car['url'])
            wait_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")

            # Iterate over DataPacks tables TR 
            for car_element in iter_dom(driver, "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr"):

                wait_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")

                #print(car_element.get_attribute('innerHTML'))

                print("Start building datapack for {}".format(car['car']))

                # Set tracks counter
                row_count = 1

                #print('car_element: ',car_element.find_element_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[1]/td/div/div").get_attribute('innerHTML'))


                # Start from 2nd line if "Previous weeks" line exists
                #try:
                #    if driver.find_element_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[1]/td/div/div").text.lower().strip() == "show previous weeks":
                #       row_count = 2
                #    else:
                #        test = driver.find_element_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[1]/td/div/div").get_attribute('innerHTML')
                #        print(driver.current_url)
                #        print('test: ', '_' + test + '_')
                #except Exception as e:
                #    print('ERR', e)
                #    continue

                # Jump to second row if first iteration
                if row_count == 1 and check_exists_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[1]/td/div/div"):
                    row_count += 1 


                print('row_count', row_count)
 
                # Create datapacks list
                datapack = {}

                # Build datapack (only one registered atm)
                try:
                    #print("table", driver.find_elements_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']"))

                    # Build fom tracks lists
                    #print(driver.find_elements_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[" + str(row_count) + "]/td[2]/div/img"))

                    datapack['track'] = driver.find_elements_by_xpath(
                        "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[" + str(row_count) + "]/td[2]/div/img"
                        )[0].get_attribute('title')

                    datapack['fastest_laptime'] = driver.find_elements_by_xpath(
                        "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[" + str(row_count) + "]/td[3]/div/span[1]/span"
                        )[0].get_attribute('title')

                    datapack['time_of_day'] = driver.find_elements_by_xpath(
                        "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[" + str(row_count) + "]/td[4]/div/span[1]/span"
                        )[0].get_attribute('title')
                        
                    datapack['track_state'] = driver.find_elements_by_xpath(
                        "//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[" + str(row_count) + "]/td[4]/div/span[2]/span"
                        )[0].get_attribute('title')


                    car['datapacks'].append(datapack)

                    print('datapack: ', datapack)

                    row_count += 1

                except Exception as e:
                    print('ERR', e)
                    #traceback.print_stack()
                    continue


                row_count += 1

            
            #    if datapack['fastest_laptime'] != "":
            #        car_element.find_element_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr[" + str(row_count) + "]/td[7]/a").click()
            #        time.sleep(3)
#
            #        datapack['files'] = []
            #        for line in driver.find_elements_by_css_selector("form.session-file-name"):
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
            #                filename = str(file.text).replace(' .','.').replace(' ','_').lower()
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

            
            
            print(json.dumps(car, indent=4))

build_datapacks_infos(cars_list)

#print(json.dumps(cars_list, indent=4))


# Finaly close the browser
driver.close()


