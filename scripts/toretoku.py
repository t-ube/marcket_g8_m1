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

class toretokuListParser():
    def __init__(self, _html):
        self.__html = _html
        self.__reject = ['デッキ','ケース','プレイマット','スリーブ']
        #(キラ)/

    def getItemList(self,keyword):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        divList = soup.find_all("div", class_="js_cartInsertInfo cartInsertInfo")
        for div in divList:
            nameElm = self.getNameElm(div)
            name = self.getItemName(nameElm)
            find = False
            for reject in self.__reject:
                if reject in name:
                    find = True
                    break
            if find == False and self.keywordInName(keyword,name):
                l.append({
                    "market": 'toretoku',
                    "link": self.getLink(nameElm),
                    "price": int(re.findall('[0-9]+', self.getPrice(div).replace(',',''))[0]),
                    "name": '{:.10}'.format(name),
                    #"image": self.getImage(a),
                    "date": None,
                    "datetime": None,
                    "stock": self.getStock(div),
                })
        return l

    def keywordInName(self,keyword,name):
        if keyword in name:
            return True
        if keyword.replace('　',' ').replace(' ','') in name.replace('　',' ').replace(' ',''):
            return True
        return False
    
    def getPrice(self,_BeautifulSoup):
        div = _BeautifulSoup.find("div", class_="price flex flex-space-between")
        if div is not None:
            return div.get_text()
        return None

    def getNameElm(self,_BeautifulSoup):
        p = _BeautifulSoup.find("p", class_="name")
        if p is not None:
            a = p.find("a")
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
        img = _BeautifulSoup.find("img")
        if img is not None:
            if img.has_attr('src'):
                return img['src']
        return None

    def getStock(self,_BeautifulSoup):
        p = _BeautifulSoup.find("p", class_="stock")
        if p is not None:
            find_pattern = r"(?P<c>[0-9]+)"
            m = re.search(find_pattern, p.get_text())
            if m != None:
                return int(m.group('c'))
        return 0


class toretokuSearchCsv():
    def __init__(self,_out_dir):
        dt = jst.now().replace(microsecond=0)
        self.__out_dir = _out_dir
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_toretoku.csv'

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

class toretokuCsvBot():
    def download(self, drvWrapper, keyword, collection_num, out_dir):
        
        # カード一覧へ移動
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        csv = toretokuSearchCsv(out_dir)

        self.getResultPageNormal(drvWrapper.getDriver(), self.getNewKey(keyword,collection_num))
        drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'resultList')))
        #time.sleep(1)
        listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
        parser = toretokuListParser(listHtml)
        l = parser.getItemList(keyword)
        for item in l:
            csv.add(item)
            print(item)
        csv.save()
        
    def getResultPageNormal(self, driver, keyword):
        url = 'https://www.toretoku.jp/item?'
        url += '&genre=5&sortIndex=5'
        url += '&kw='+keyword
        url += '&priceFrom=&priceTo=&stock=&discount='
        print(url)
        driver.get(url)

    def getNewKey(self, keyword, collection_num):
        if 'V-UNION' in keyword and 'モルペコ' in keyword:
            if '226' in collection_num or '227' in collection_num or '228' in collection_num or '229' in collection_num:
                newkey = keyword+' '+'CSR'
            else:
                newkey = keyword+' '+'RRR'
        else:
            newkey = keyword+' '+collection_num
        return newkey
