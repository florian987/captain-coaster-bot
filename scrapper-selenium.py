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


driver = webdriver.Chrome()
#driver = webdriver.Firefox(proxy=proxy)
#driver.implicitly_wait(10) # seconds
#driver.get("http://virtualracingschool.appspot.com/#/DataPacks")
#driver.add_cookie({"host":"virtualracingschool.appspot.com","domain":"virtualracingschool.appspot.com","secure":False,"expire":1533023830,"name":"vrs","value":"zkXqnElNVioRWuUK1JgojA"})
driver.get("https://virtualracingschool.appspot.com/#/DataPacks")

time.sleep(10)

row_nodes = driver.find_elements_by_xpath("//table[@data-vrs-widget='tableWrapper']/tbody/tr")

#print(row_nodes)

iracing_series = []

for row in row_nodes:
    #print(row.find_element_by_css_selector('td:nth-of-type(1)'))
    #print(row.find_element_by_css_selector('td:nth-of-type(3)').text)
    
    node_serie = row.find_element_by_css_selector('td:nth-of-type(1) img').get_attribute('title')
    node_car = row.find_element_by_css_selector('td:nth-of-type(2) img').get_attribute('title')
    node_season = row.find_element_by_css_selector('td:nth-of-type(3)').text
    node_author = row.find_element_by_css_selector('td:nth-of-type(4) img').get_attribute('title')
    #print(serie_node)

    print(row.find_element_by_xpath("//span[@data-vrs-widget-field='packIdElement']").get_attribute("innerHTML"))
    print(row.find_element_by_css_selector("p:nth-of-type(1)").get_attribute("innerHTML"))

    #iracing_series.append(serie_node)

    datapack = {}
    datapack['serie'] = node_serie
    datapack['car'] = node_car
    datapack['season'] = node_season
    datapack['author'] = node_author

    print(json.dumps(datapack, indent=4))

    #print(img_node.get_attribute('src'), img_node.get_attribute('title'), img_node.get_attribute('alt'))

#print(json.dumps(datapack, indent=4))

#html = driver.page_source

#wait = WebDriverWait(driver, 15)
#element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'card-content')))

#html = driver.execute_script('return document.documentElement.outerHTML')

#soup = BeautifulSoup(html, 'lxml')

#print(html)

#for line in html:
#    if "25590001" in line:
#        print('SAMARCHE')

#try:
#    element = WebDriverWait(driver, 10).until(
#        EC.presence_of_element_located((By.ID, "myDynamicElement"))
#    )
#finally:
#    driver.quit()


driver.close()


