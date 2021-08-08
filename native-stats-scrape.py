##################################
# Build in: MacOS Big Sur 11.5.1 #
# Coding: UTF-8                  #
# Author: Nitro                  #
# Status: Development            #
# Version: 0.0.1                 #
# Update at: 6th August 2021     #
##################################

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from datetime import datetime
import argparse
import codecs
import json
import os
import sys

def setup_driver(driver_path):
    ''' Setup chrome browser

    :param driver_path: chrome driver path
    :return: chrome driver
    '''
    options = webdriver.ChromeOptions()
    prefs =  {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    return driver


def get_element(driver, xpath, skip_word=None):
    ''' Get element with xpath
    
    :param driver: chrome driver
    :param xpath: xpath for keyword
    :param skip_word: specific word need to be excluded
    :return: web element's content
    :raise errors: break if no elements found
    '''
    if skip_word is None:
        try:
            keyword = driver.find_element_by_xpath(xpath=xpath).text
        except NoSuchElementException:
            print(f"Please check with the xpath: {xpath}")
            keyword = "null"
    else:
        try:
            keyword_list = driver.find_elements_by_xpath(xpath=xpath)
            keyword = [keyword.text for keyword in keyword_list if not keyword.text == skip_word][0]
        except NoSuchElementException:
            keyword = "null"
    return keyword


def get_element_list(driver, xpath, header=["number", "name", "position", "market_value"], skip_word="Total market value:"):
    ''' Get elements with xpath and wrap in order
    
    :param driver: chrome driver
    :param xpath: xpath for keyword
    :param target: keyword for targets
    :param header: header of the table
    :return: list of target content
    :raise errors: break if no elements found
    '''
    try:
        table = (By.XPATH, xpath)
        jobs = driver.find_element(*table).find_elements(By.TAG_NAME, "tr")
        fields = [job.find_elements_by_tag_name("td") for job in jobs]
        contents = [field.text for field in fields if not field.text == skip_word]
        if header is None:
            keywords = contents
        else:
            keywords = [dict(zip(header, content)) for content in contents]
    except NoSuchElementException:
        keywords = ["null"]
    return keywords


def get_attribute_list(driver, xpath, attribute, skip_word=None):
    ''' Get attribute with xpath
    
    :param driver: chrome driver
    :param xpath: xpath for keyword
    :param attribute: specific attribute need to be extracted 
    :param skip_word: specific word need to be excluded
    :return: web element's attribute
    :raise errors: break if no attributes found
    '''
    if skip_word is None:
        keyword_list = driver.find_elements_by_xpath(xpath=xpath)
        keywords = [keyword.get_attribute(attribute) for keyword in keyword_list]
    else:
        keyword_list = driver.find_elements_by_xpath(xpath=xpath)
        keywords = [keyword.get_attribute(attribute) for keyword in keyword_list if not keyword.text == skip_word]
    return keywords


def home_page_info(scrape_page, driver, save_path):
    ''' Visit home page and get match outline

    :param scrape_page: desired page to scrape
    :param driver: chrome driver
    :param save_path: folder to save data
    :return: all match ids and match ouline ouput json file
    :raise errors: break if timeout
    '''
    try:
        driver.get(scrape_page)
        WebDriverWait(driver, 5, 0.5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='container']")))
        ids = get_attribute_list(driver=driver, xpath="//tr[@class='open_match_view']", attribute="id")
        home_page_list = []
        for id in ids:
            match_outline = {
                "id": id,
                "url": "{}/matches/{}".format(scrape_page, id),
                "datetime": {
                    "match_date": get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='datetime']/span[contains(@class, 'match_date')]"),
                    "match_time": get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='datetime']/span[contains(@class, 'match_time')]"),
                    "badge":  get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='datetime']/span[contains(@class, 'badge')]")
                },
                "matchday": get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='matchday']"),
                "fixture": {
                    "home_team": get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='fixture']/span[@class='homeTeam']/span[@class='ls-only']"),
                    "away_team": get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='fixture']/span[@class='homeTeam']/span[@class='ls-only']", skip_word=".vs")
                },
                "score": get_element(driver=driver, xpath=f"//tr[@id='{id}']/td[@class='score']")
            }
            home_page_list.append(match_outline)
        driver.quit()
        save_name = "native-stats-home_{}.json".format(datetime.now().strftime('%Y-%m-%d'))
        with codecs.open(filename=os.path.join(save_path, save_name), mode="w", encoding="UTF-8", errors="ignore") as home_page:
            home_page.write(json.dumps(home_page_list, ensure_ascii=False))
        
    except TimeoutException:
        print("Timeout exception, home page took too long to load.")
        driver.quit()
        sys.exit(1)

    return ids


def match_page_info(scrape_page, id, driver):
    ''' View detailed match status and get infomation

    :param ids desired page id to scrape
    :param driver: chrome driver
    :param save_path: folder to save data
    :return: status code and match details saved in dictionary
    :raise errors: break if timeout
    '''
    try:
        driver.get("{}/matches/{}".format(scrape_page, id))
        WebDriverWait(driver, 5, 0.5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='container']")))
        if get_element(driver=driver, xpath=f"//div[@class='h4']") == "No time yet to build a proper error page, but be sure that something went wrong.":
            match_info = {
                "id": id,
                "url": "{}/matches/{}".format(scrape_page, id),
                "status": "error"
            }
        else:
            match_info = {
                "id": id,
                "url": "{}/matches/{}".format(scrape_page, id),
                "status": "loaded",
                "home_team": {
                    "lineup": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[1]/table[1]/tbody"),
                    "bench": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[1]/table[2]/tbody")
                },
                "away_team": {
                    "lineup": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[2]/table[1]/tbody"),
                    "bench": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[2]/table[2]/tbody")
                },
                "statics": {
                    "goals": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[3]/table[1]/tbody", header=["minute", "team", "scorer", "assist"], skip_word=None),
                    "substitutions": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[3]/table[2]/tbody", header=["minute", "team", "player_in", "player_out"], skip_word=None),
                    "bookings": get_element_list(driver=driver, xpath="//div[@id='content']/div[3]/div[3]/table[3]/tbody", header=["minute", "team", "player", "card"], skip_word=None)
                },
                "head2head": get_element_list(driver=driver, xpath="//div[@id='content']/div[4]/div[1]/table/tbody", header=None, skip_word=None),
                "encounters": get_element_list(driver=driver, xpath="//div[@id='content']/div[4]/div[2]/table/tbody", header=None, skip_word=None)
            }

    except TimeoutException:   
        print("Timeout exception, match page took too long to load.")
        driver.quit()
        sys.exit(1)

    return match_info


def parse_args(argv):
    ''' Parse all arguments

    :param argv: string of sys arguments passed to command line
    :return: arguments parsed out result
    '''
    parser = argparse.ArgumentParser(description='Download match data from Native Stats.')
    # Parse Scrape Page
    parser.add_argument("--scrape-page",
                    dest = "scrapepage",
                    type = str,
                    default= "https://native-stats.org",
                    help = "Enter the desired page of different league.")
    # Parse Save Path
    parser.add_argument("--save-dir",
                    dest = "savepath",
                    default = os.path.expanduser("~") + "/Downloads/",
                    help = "Argument to specify the download path where files will go.")
    # Parse Driver Path
    parser.add_argument("--driver-dir",
                    dest = "driverpath",
                    default = "/opt/homebrew/bin/chromedriver",
                    help = "Optional argument to locate the chrome driver.")
    # Return help message if no arguments provided
    if len(argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_args(argv)
    # Define Scrape Page
    scrape_page = args.scrapepage
    # Define Save Path
    save_path = args.savepath
    if not os.path.exists(save_path):
        print("The download destination directory specified does not exist, defaulting to save on desktop.")
        save_path = os.path.expanduser("~") + "/Desktop/"
    # Define Driver Path
    driver_path = args.driverpath
    if not os.path.exists(driver_path):
        print("The download destination directory specified does not exist, defaulting to Downloads folder.")
        driver_path = "/opt/homebrew/bin/chromedriver"
    # Main Scraping Process
    driver = setup_driver(driver_path=driver_path)
    ids = home_page_info(scrape_page=scrape_page, driver=driver, save_path=save_path)
    match_page_list = [match_page_info(scrape_page=scrape_page, id=id, driver=driver) for id in ids]
    save_name = "native-stats-match_{}.json".format(datetime.now().strftime('%Y-%m-%d'))
    with codecs.open(filename=os.path.join(save_path, save_name), mode="w", encoding="UTF-8", errors="ignore") as match_page:
        match_page.write(json.dumps(match_page_list, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))