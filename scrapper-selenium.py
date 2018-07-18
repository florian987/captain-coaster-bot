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


    
## Get cookie from file
#with open("./cookie", "r") as cookie_file:
#    for line in cookie_file:
#        if "jsessionid" in line.lower():
#            cookie = dict(JSESSIONID=line.split("=")[1])
#            print(cookie)

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
        datapack = {}
        datapack['serie'] = node_serie
        datapack['car'] = node_car
        datapack['season'] = node_season
        datapack['author'] = node_author
        datapack['id'] = node_id
        datapack['premium'] = node_premium

        iracing_cars.append(datapack)

        #print(json.dumps(datapack, indent=4))

        #print(img_node.get_attribute('src'), img_node.get_attribute('title'), img_node.get_attribute('alt'))

    # debug cars list
    print(json.dumps(iracing_cars, indent=4))

    # Return cars list
    return iracing_cars

cars_list = build_cars_list()

for car in cars_list:
    if car['premium'] == False:
        driver.get("https://virtualracingschool.appspot.com/#/DataPacks/" + car['id'])

        # Wait dégueulasse pour load le JS
        time.sleep(3)

        # Retrieve cars table
        row_nodes = driver.find_elements_by_xpath("//table[@data-vrs-widget='DataPackWeeksTable']/tbody/tr")

# Implicit selenium wait test
#try:
#    element = WebDriverWait(driver, 10).until(
#        EC.presence_of_element_located((By.ID, "myDynamicElement"))
#    )
#finally:
#    driver.quit()


driver.close()


