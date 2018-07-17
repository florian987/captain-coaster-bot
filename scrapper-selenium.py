# -*- coding: utf-8 -*-

import os

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


driver = webdriver.Firefox(proxy=proxy)
#driver.implicitly_wait(10) # seconds
driver.get("http://virtualracingschool.appspot.com/#/DataPacks")
driver.add_cookie({"host":"virtualracingschool.appspot.com","domain":"virtualracingschool.appspot.com","secure":False,"expire":1533023830,"name":"vrs","value":"zkXqnElNVioRWuUK1JgojA"})
driver.get("https://virtualracingschool.appspot.com/#/DataPacks")

#html = driver.page_source
html = driver.execute_script('return document.documentElement.outerHTML')

#soup = BeautifulSoup(html, 'lxml')

print(html)

#for line in html:
#    if "25590001" in line:
#        print('SAMARCHE')

#try:
#    element = WebDriverWait(driver, 10).until(
#        EC.presence_of_element_located((By.ID, "myDynamicElement"))
#    )
#finally:
#    driver.quit()

#assert "Python" in driver.title
#driver.implicitly_wait(1) # seconds
#elem = driver.find_element_by_css_selector('a').click()
card_content = driver.find_elements_by_class_name("card-content")
body = driver.find_element_by_tag_name('body')

print(body)

#elem = card_content.get_attribute('innerHTML')
#
#print(elem)

#for row in data_pack_rows:
#    print(row)
#elem.clear()
#elem.send_keys("pycon")
#elem.send_keys(Keys.RETURN)
#assert "No results found." not in driver.page_source
#driver.close()




#print(cookie_vrs)

#
#r = requests.get(url, cookies=cookie_vrs)
#print(r.text)
#
#for line in r.text:
#    if "pack" in line.lower():
#        print(line)