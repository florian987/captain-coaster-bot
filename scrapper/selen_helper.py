import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def build_driver(headless=True, log_path=None):
    """
    Build a selenium driver for the desired browser with its parameters
    """
    # TODO Implement firefox, waiting for selenium 3.14.0 to fix timeout
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    DL_DIR = os.path.join(ROOT_DIR, 'tmp')
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {
        "download.default_directory": DL_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False
    })
    if headless:
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        options.add_argument('no-sandbox')

    # Build Chrome driver
    driver = webdriver.Chrome(chrome_options=options, service_log_path=log_path)
    # Add devtools command to allow download
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': DL_DIR
    })
    driver.set_page_load_timeout(90)

    return driver


def check_exists_by_xpath(driver, xpath):
    """check if an element exists by its xpath"""
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True


def wait_by_id(driver, id, retries=20):
    """
    Wait for element to load by ID
    """
    try:
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.ID, id)))
    except Exception:
        print(f"Unable to find element {id} in page")
        return False
    return True


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
    """
    Wait for xpath element to load
    """
    try:
        # element = WebDriverWait(driver, retries).until(
        WebDriverWait(driver, retries).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
    except Exception:
        print(f"Unable to find element {xpath} in page")

