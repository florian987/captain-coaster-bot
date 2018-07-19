# -*- coding: utf-8 -*-

import os
import time
import json

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Proxy Settings
PROXY = "fw_in.bnf.fr:8080"

proxy = Proxy({
    'proxyType': ProxyType.MANUAL,
    'httpProxy': PROXY,
    'ftpProxy': PROXY,
    'sslProxy': PROXY,
    'noProxy': '' # set this value as desired
    })



# Get cookie from file
#with open("./cookie", "r") as cookie_file:
#    for line in cookie_file:
#        print(line)
#        cookie = line



# Initialize selenium driver
driver = webdriver.Chrome()
#driver = webdriver.Firefox(proxy=proxy) # Ajout du proxy

#driver.implicitly_wait(10) # seconds
#driver.get("http://virtualracingschool.appspot.com/#/DataPacks")
#driver.add_cookie({"host":"virtualracingschool.appspot.com","domain":"virtualracingschool.appspot.com","secure":False,"expire":1533023830,"name":"vrs","value":"zkXqnElNVioRWuUK1JgojA"})

def build_cars_list():
    driver.get("https://virtualracingschool.appspot.com/#/DataPacks")

    # Wait dégueulasse pour load le JS
    time.sleep(3)

    # Retrieve cars table
    row_nodes = driver.find_elements_by_xpath("//table[@data-vrs-widget='tableWrapper']/tbody/tr")

    #print(row_nodes)

    # Initialize cars array
    iracing_cars = []

    # Iterate over table rows
    for row in row_nodes:
        #print(row.find_element_by_css_selector('td:nth-of-type(1)'))
        #print(row.find_element_by_css_selector('td:nth-of-type(3)').text)
        
        # Retrieve cars infos
        node_serie = row.find_element_by_css_selector('td:nth-of-type(1) img').get_attribute('title')
        node_car = row.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('title')
        node_season = row.find_element_by_css_selector('td:nth-of-type(3)').text
        node_author = row.find_element_by_css_selector('td:nth-of-type(4) img').get_attribute('title')
        #print(serie_node)

        # Set premium status depending of style display
        if "visible" in row.find_element_by_class_name('blue').get_attribute('style'):
            node_premium = True
        else:
            node_premium = False

        #print(row.find_element_by_xpath("//span[@data-vrs-widget-field='packIdElement']").get_attribute("innerHTML"))

        # Get car ID
        node_span = row.find_element_by_css_selector("p:nth-of-type(1)").get_attribute("innerHTML")
        soup = BeautifulSoup(node_span, "html.parser")
        for span in soup.findAll("span", attrs={"data-vrs-widget-field":"packIdElement"}):
            node_id = span.text

        #iracing_series.append(serie_node)

        # Create car dict
        car = {}
        car['serie'] = node_serie
        car['car'] = node_car
        car['season'] = node_season
        car['author'] = node_author
        car['id'] = node_id
        car['premium'] = node_premium

        iracing_cars.append(car)

        #print(json.dumps(datapack, indent=4))

        #print(img_node.get_attribute('src'), img_node.get_attribute('title'), img_node.get_attribute('alt'))

    # debug cars list
    #print(json.dumps(iracing_cars, indent=4))

    # Return cars list
    return iracing_cars

cars_list = build_cars_list()

for car in cars_list:

    # Initialize datapacks list
    car['datapacks'] = []

    # Only iterate over free cars
    if car['premium'] == False:
        driver.get("https://virtualracingschool.appspot.com/#/DataPacks/" + car['id'])

        # Wait dégueulasse pour load le JS
        time.sleep(3)

        # Retrieve cars table
        row_nodes = driver.find_elements_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")

        for row in row_nodes:

            # Create datapacks list
            datapack = {}


            try:
                # Build fom tracks lists
                datapack['track'] = row.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('title')
                datapack['fastest_laptime'] = row.find_element_by_css_selector('td:nth-of-type(3) span:nth-of-type(1) span:nth-of-type(1)').get_attribute('title')
                datapack['time_of_day'] = row.find_element_by_css_selector('td:nth-of-type(4) span:nth-of-type(1) span').get_attribute('title')
                datapack['track_state'] = row.find_element_by_css_selector('td:nth-of-type(4) span:nth-of-type(2) span').get_attribute('title')

                car['datapacks'].append(datapack)

                #print(datapack)

                # GoTo DataPack Page
                goto_datapack = row.find_element_by_css_selector('td:nth-of-type(7) a').click()

                goto_datapack

                time.sleep(3)

                session_files = driver.find_elements_by_css_selector("div.vrs-list-view")
                print(len(session_files))
                print(session_files.get_attribute("innerHTML"))

                for session_row in session_files:
                    file_name = session_row.find_elements_by_css_selector("form.session-file-name div a ").text()
                    file_grab = session_row.find_elements_by_css_selector("form.session-file-name div a").click()

                    print(file_name)
                driver.back()


                car['datapacks'].append(datapack)

            except:
                continue

            

            #goto_datapack = row.find_element_by_css_selector('td:nth-of-type(7) a').click()


            #datapack['track'] = row.find_element_by_xpath("//td[2]/div/span[1]").get_attribute("innerHTML")

            #laptime_span = row.find_element_by_css_selector("td:nth-of-type(3)").get_attribute("innerHTML")
            #soup = BeautifulSoup(node_span, "html.parser")
            #for span in soup.findAll("span", attrs={"data-vrs-widget-field":"packIdElement"}):
            #    node_id = span.text
            # lap-time-widget

            
            
        print(json.dumps(car, indent=4))

#print(json.dumps(cars_list, indent=4))

# Implicit selenium wait test
#try:
#    element = WebDriverWait(driver, 10).until(
#        EC.presence_of_element_located((By.ID, "myDynamicElement"))
#    )
#finally:
#    driver.quit()


driver.close()


