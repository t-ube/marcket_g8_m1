import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

class seleniumDriverWrapper():
    def __init__(self):
        self.__driver = None
        self.__wait = None

    def begin(self,webdriver):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--start-maximized')
        options.set_capability('pageLoadStrategy', 'eager')
        self.__driver = webdriver.Chrome(options=options)
        self.__wait = WebDriverWait(driver=self.__driver, timeout=30)
        self.__driver.execute_script("window.open()")
        self.__driver.switch_to.window(self.__driver.window_handles[1])

    def getDriver(self):
        return self.__driver

    def getWait(self):
        self.__wait = WebDriverWait(driver=self.__driver, timeout=5)
        return self.__wait

    def end(self):
        self.__driver.quit()

    def clickXPath(self,xpath):
        element = WebDriverWait(self.__driver, 10).until(lambda x: x.find_element(By.XPATH,xpath))
        #element = self.__driver.find_element(By.XPATH,xpath)
        element.click()

    def inputXPath(self,xpath,text):
        element = self.__driver.find_element(By.XPATH,xpath)
        element.send_keys(text)
