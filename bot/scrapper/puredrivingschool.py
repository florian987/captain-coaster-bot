# -*- coding: utf-8 -*-

# import pickle
# import traceback
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


script_dir = os.path.dirname(os.path.realpath(__file__))
download_dir = os.path.join(script_dir, "downloads")
log_dir = os.path.join(script_dir, "logs")
gecko_log_path = os.path.join(log_dir, "geckodriver.log")

needed_dirs = [
    download_dir,
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
            options.add_argument('disable-gpu')
        driver = webdriver.Chrome(chrome_options=options)
        driver.execute_cdp_cmd(  # Add devtools command to allow download
            'Page.setDownloadBehavior',
            {'behavior': 'allow', 'downloadPath': download_dir}
        )

    elif browser == "Firefox":  # Handle Firefox profile
        profile = webdriver.FirefoxProfile()
        profile.set_preference(
            'browser.download.folderList', 2  # custom location
        )
        profile.set_preference(
            'browser.download.manager.showWhenStarting', False
        )
        profile.set_preference('browser.download.dir', download_dir)
        profile.set_preference('browser.download.downloadDir', download_dir)
        profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk', 'application/zip'
        )
        profile.set_preference(
            'browser.helperApps.neverAsk.saveToDisk',
            'application/octet-stream'
        )
        driver = webdriver.Firefox(profile, log_path=gecko_log_path)

    # Set global driver settings
    driver.set_page_load_timeout(90)

    return driver


def iter_dom(driver, xpath):
    """
    Iterate over dom elements to avoid losing focus.
    """
    def get_next_element(elems, idx):
        for i, element in enumerate(elems):
            if i == idx:
                return element

    current_idx = 0
    has_elements = True
    while has_elements:
        elements = driver.find_elements_by_xpath(xpath)
        try:
            elem = get_next_element(elements, current_idx)
            if elem:
                yield elem
        except Exception as e:
            elements = driver.find_elements_by_xpath(xpath)
            elem = get_next_element(elements, current_idx)
            if elem:
                yield elem

        if elem:
            current_idx += 1
        else:
            has_elements = False


def wait_by_xpath(driver, xpath, retries=20):
    """Wait for xpath element to load"""
    try:
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
    except Exception:
        print(f"Unable to find element {xpath} in page")


def wait_by_css(driver, css, retries=20):
    """Wait for css element to load"""
    try:
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


def download_img(url, dest=None):
    """
    Download an image weither specifying or not its destination.
    Register using filename from url. In cwd if dest is not set
    """

    filename = url.split('/')[-1]   # Set filename from url
    if dest is None:
        file_dest = filename
    else:
        if "." not in dest.split('/')[-1]:  # If filename not in dest
            file_dest = os.path.join(dest, filename)
        else:
            file_dest = dest

    if not os.path.isfile(file_dest):  # Download if not exists
        urllib.request.urlretrieve(url, file_dest)
