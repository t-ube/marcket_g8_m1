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
import datetime
import re
from . import jst
from . import seleniumDriverWrapper as wrap
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import traceback

class torecoloListParser():
    def __init__(self, _html):
        self.__html = _html
        self.__reject = ['デッキ','ケース','プレイマット','スリーブ']
        #ミラー仕様/通常仕様

    def getItemList(self,keyword):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        dlList = soup.find_all("dl", class_="block-thumbnail-t--goods")
        for dl in dlList:
            nameElm = self.getNameElm(dl)
            name = self.getItemName(nameElm)
            find = False
            for reject in self.__reject:
                if reject in name:
                    find = True
                    break

            if find == False and self.keywordInName(keyword,name):
                l.append({
                    "market": 'torecolo',
                    "link": self.getLink(nameElm),
                    "price": int(re.findall('[0-9]+', self.getPrice(dl).replace(',',''))[0]),
                    "name": '{:.10}'.format(name),
                    #"image": self.getImage(a),
                    "date": None,
                    "datetime": None,
                    "stock": self.getStock(dl),
                })
        return l

    def keywordInName(self,keyword,name):
        if keyword in name:
            return True
        if keyword.replace('　',' ').replace(' ','') in name.replace('　',' ').replace(' ',''):
            return True
        return False
    
    def getPrice(self,_BeautifulSoup):
        div = _BeautifulSoup.find("div", class_="block-thumbnail-t--price price js-enhanced-ecommerce-goods-price")
        if div is not None:
            return div.get_text()
        return None

    def getNameElm(self,_BeautifulSoup):
        a = _BeautifulSoup.find("a", class_="js-enhanced-ecommerce-goods-name")
        if a is not None:
            return a
        return None
    
    def getItemName(self,_BeautifulSoup):
        if _BeautifulSoup.has_attr('title'):
           return _BeautifulSoup['title']
        return None

    def getLink(self,_BeautifulSoup):
        if _BeautifulSoup.has_attr('href'):
           return _BeautifulSoup['href']
        return None

    def getImage(self,_BeautifulSoup):
        img = _BeautifulSoup.find("img", class_=" lazyloaded")
        if img is not None:
            if img.has_attr('src'):
                return img['src']
        return None

    def getStock(self,_BeautifulSoup):
        div = _BeautifulSoup.find("div", class_="block-thumbnail-t--stock")
        if div is not None:
            find_pattern = r"(?P<c>[0-9]+)"
            m = re.search(find_pattern, div.get_text())
            if m != None:
                return int(m.group('c'))
        return 0

class torecoloSearchCsv():
    def __init__(self,_out_dir):
        dt = jst.now().replace(microsecond=0)
        self.__out_dir = _out_dir
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_torecolo.csv'

    def init(self):
        labels = [
         'market'
         'link',
         'price',
         'name', 
         #'image',
         'date',
         'datetime',
         'stock'
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
        df = pd.DataFrame.from_dict(self.__list)
        if os.path.isfile(self.__file) == False:
            self.init()
        df.to_csv(self.__file, index=False, encoding='utf_8_sig')

class torecoloCsvBot():
    def download(self, drvWrapper, keyword, collection_num, out_dir):
        # カード一覧へ移動
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        csv = torecoloSearchCsv(out_dir)

        self.getResultPageNormal(drvWrapper.getDriver(), self.getNewKey(keyword,collection_num))

        try:
            drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'block-thumbnail-t')))
            #time.sleep(3)
            listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
            parser = torecoloListParser(listHtml)
            l = parser.getItemList(keyword)
            for item in l:
                csv.add(item)
                print(item)
            csv.save()
        except TimeoutException as e:
            print("TimeoutException")
        except Exception as e:
            print(traceback.format_exc())
    
    def getResultPageNormal(self, driver, keyword):
        url = 'https://www.torecolo.jp/shop/goods/search.aspx?ct2=1074&search=x&keyword='+keyword
        url += '&search=search'
        print(url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())

    def getNewKey(self, keyword, collection_num):
        keyword = keyword.replace('V-UNION','Ｖ－ＵＮＩＯＮ')
        newkey = keyword+'+'+collection_num
        return newkey
