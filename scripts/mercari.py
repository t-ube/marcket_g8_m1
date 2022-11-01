import requests
import urllib.request
from concurrent import futures
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import time
import csv
import json
import os
import sys
import math
import datetime
import re
from . import jst
from . import seleniumDriverWrapper as wrap
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class mercariListParser():
    def __init__(self, _html):
        self.__html = _html
        self.__reject = ['デッキ','ケース','専用','様','スリーブ','オリパ','海外']

    
    def getItemList(self,keyword):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        aList = soup.find_all("a", class_="ItemGrid__StyledThumbnailLink-sc-14pfel3-2")
        for a in aList:
            thum = self.getThumnail(a)
            if thum is None:
                continue
            name = self.getItemName(thum)
            if name is None:
                continue
            find = False
            for reject in self.__reject:
                if reject in name:
                    find = True
                    break
            if find == False and self.keywordInName(keyword,name):
                price = int(self.getPrice(thum).replace("¥ ","").replace(",","").replace(" ",""))
                priceTemp = self.getTitlePrice(name)
                setNumber = self.getSetNumber(name)
                stock = 1
                if priceTemp is not None:
                    price = priceTemp
                elif setNumber is not None:
                    stock = setNumber
                    price = math.floor(price/setNumber)
                    if price < 1:
                        price = 1
                if int(price) < 999999:
                    l.append({
                        "market": 'mercari',
                        "link": a['href'],
                        "price": price,
                        "name": '{:.10}'.format(name),
                        #"image": self.getImage(a),
                        "date": None,
                        "datetime": None,
                        "stock": stock,
                    })
        return l

    def keywordInName(self,keyword,name):
        if keyword in name:
            return True
        new_key = keyword.replace('　',' ').replace(' ','').replace('（','').replace('）','').replace('[','').replace(']','').replace('(','').replace(')','')
        new_name = name.replace('　',' ').replace(' ','').replace('（','').replace('）','').replace('[','').replace(']','').replace('(','').replace(')','')
        if new_key in new_name:
            return True
        return False

    def getTitlePrice(self, keyword):
        find_pattern = r'1枚(?P<x>\d+)円'
        m = re.search(find_pattern, keyword)
        if m != None:
            return int(m.group('x'))
        return None

    def getSetNumber(self, keyword):
        find_pattern = r'(?P<x>\d+)枚セット'
        m = re.search(find_pattern, keyword)
        if m != None:
            return int(m.group('x'))
        return None

    def getThumnail(self,_BeautifulSoup):
        thum = _BeautifulSoup.find("mer-item-thumbnail")
        if thum is not None:
            return thum
        return None
    
    def getPrice(self,_BeautifulSoup):
        if _BeautifulSoup.has_attr('price'):
            return _BeautifulSoup['price']
        return None
    
    def getItemName(self,_BeautifulSoup):
        if _BeautifulSoup.has_attr('alt'):
            return _BeautifulSoup['alt']
        return None

    def getImage(self,_BeautifulSoup):
        if _BeautifulSoup.has_attr('src'):
            return _BeautifulSoup['src']
        return None

    def isNext(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        buttons = soup.find_all("mer-button")
        for btn in buttons:
            if btn.has_attr('data-testid'):
                if btn['data-testid'] == 'pagination-next-button':
                    return True
        return False

class mercariSearchCsv():
    def __init__(self,_out_dir):
        dt = jst.now().replace(microsecond=0)
        self.__out_dir = _out_dir
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_mercari.csv'

    def init(self):
        labels = [
         'market'
         'link',
         'price',
         'name', 
         #'image',
         'date',
         'datetime'
         ]
        try:
            with open(self.__file, 'w', newline="", encoding="utf_8_sig") as f:
                writer = csv.DictWriter(f, fieldnames=labels)
                writer.writeheader()
                f.close()
        except IOError:
            print("I/O error")

    def add(self, data):
        data['date'] = str(self.__date)
        data['datetime'] = str(self.__datetime)
        self.__list.append(data)
        
    def save(self):
        if len(self.__list) == 0:
            return
        
        labels = [
         'market'
         'link',
         'price',
         'name', 
         #'image',
         'date',
         'datetime'
         ]
        df = pd.DataFrame.from_dict(self.__list)
        if os.path.isfile(self.__file) == False:
            self.init()
        df.to_csv(self.__file, index=False, encoding='utf_8_sig')

class mercariCsvBot():
    def getTop(self, drvWrapper):
        drvWrapper.getDriver().get('https://jp.mercari.com/')
        drvWrapper.getWait().until(EC.visibility_of_all_elements_located)
        time.sleep(15)

    def download(self, drvWrapper, card_name, regulation, collection_num, out_dir):
        nextLoop = True
        page_number = 0
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        csv = mercariSearchCsv(out_dir)
        while nextLoop:
            page_number += 1
            print('---------------')
            print(page_number)
            print('---------------')
            if page_number == 1:
                self.getResultPageNormal(drvWrapper.getDriver(), regulation, collection_num)
            drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.ID,'item-grid')))
            time.sleep(5)
            listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
            parser = mercariListParser(listHtml)
            l = parser.getItemList(card_name)
            for item in l:
                csv.add(item)
                print(item)
            if parser.isNext() == False:
                break
            elementsBtn = drvWrapper.getDriver().find_elements(By.TAG_NAME, 'mer-button')
            nextLoop = False
            if len(elementsBtn) != 0:
                for btn in elementsBtn:
                    if btn.get_attribute("data-testid") == 'pagination-next-button':
                        nextLoop = True
                        btn.click()
        csv.save()

    def getResultPageNormal(self, driver, regulation, collection_num):
        url = 'https://jp.mercari.com/search?keyword='
        url += regulation + ' ' + collection_num + ' -処分 -まとめ -ほか -他'
        url += '&order=desc&sort=created_time&status=on_sale&category_id=1289'
        driver.get(url)
