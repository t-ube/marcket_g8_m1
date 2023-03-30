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

class dorasutaListParser():
    def __init__(self, _html):
        self.__html = _html
        self.__reject = ['デッキ','ケース','プレイマット','スリーブ']
        #<b>ミラー</b>

    def getItemList(self,keyword):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        divList = soup.find_all("div", class_="element")
        print(divList)
        if divList is None:
            return l
        for div in divList:
            name = self.getItemName(div)
            print(name)
            find = False
            for reject in self.__reject:
                if reject in name:
                    find = True
                    break
            if find == False and self.keywordInName(keyword,name):
                link = self.getLink(div)
                l.append({
                    "market": 'dorasuta',
                    "link": link,
                    "price": None,
                    "name": '{:.10}'.format(name),
                    #"image": self.getImage(li),
                    "date": None,
                    "datetime": None,
                    "stock": None,
                })
        return l

    def keywordInName(self,keyword,name):
        if keyword in name:
            return True
        if keyword.replace('　',' ').replace(' ','') in name.replace('　',' ').replace(' ',''):
            return True
        return False
    
    def getItemName(self,_BeautifulSoup):
        a = _BeautifulSoup.find("a")
        if a is not None:
            return a.get_text()
        return None

    def getLink(self,_BeautifulSoup):
        a = _BeautifulSoup.find("a")
        if a is not None:
            if a.has_attr('href'):
                return a['href']
        return None

    
class dorasutaItemParser():
    def __init__(self, _html):
        self.__html = _html

    def getItem(self,item):
        soup = BeautifulSoup(self.__html, 'html.parser')
        table = soup.find("table", class_='stock')
        if table is None:
            return None
        result = {
            "market": item['market'],
            "link": item['link'],
            "price": self.getPrice(table),
            "name": item['name'],
            "date": None,
            "datetime": None,
            "stock": self.getStock(table),
        }
        return result
    
    def getPrice(self,_BeautifulSoup):
        span = _BeautifulSoup.find("td", class_="price")
        if span is not None:
            return int(re.findall('[0-9]+', span.get_text().replace(',',''))[0])
        return None

    def getStock(self,_BeautifulSoup):
        tdList = _BeautifulSoup.find_all("td")
        if tdList is None:
            return 0
        for td in tdList:
            if td is not None:
                find_pattern = r"在庫数：(?P<c>[0-9]+)"
                m = re.search(find_pattern, td.get_text().replace(',',''))
                if m != None:
                    return int(m.group('c'))
        return 0

class dorasutaSearchCsv():
    def __init__(self,_out_dir):
        dt = jst.now().replace(microsecond=0)
        self.__out_dir = _out_dir
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_dorasuta.csv'

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

class dorasutaCsvBot():
    def download(self, drvWrapper, keyword, collection_num, out_dir):
        # カード一覧へ移動
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        csv = dorasutaSearchCsv(out_dir)

        newkey = self.getNewKey(keyword,collection_num)
        self.getResultPageNormal(drvWrapper.getDriver(), newkey)

        try:
            #drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'count')))
            time.sleep(2)
            listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
            parser = dorasutaListParser(listHtml)
            l = parser.getItemList(keyword)
            for item in l:
                self.getProductPage(drvWrapper.getDriver(), newkey)
                #drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'price')))
                time.sleep(2)
                listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
                itemParser = dorasutaItemParser(listHtml)
                writeItem = itemParser.getItem(item)
                if writeItem != None:
                    csv.add(writeItem)
                    print(writeItem)
            csv.save()
        except TimeoutException as e:
            print("TimeoutException")
        except Exception as e:
            print(traceback.format_exc())

    def getResultPageNormal(self, driver, keyword):
        url = 'https://dorasuta.jp/pokemon-card/product-list?kw='+keyword
        print(url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())

    def getProductPage(self, driver, href):
        url = 'https://dorasuta.jp'+href
        print(url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())

    def getNewKey(self, keyword, collection_num):
        if 'V-UNION' in keyword and 'モルペコ' in keyword:
            if '226' in collection_num or '227' in collection_num or '228' in collection_num or '229' in collection_num:
                newkey = urllib.parse.quote(keyword+' '+'CSR')
            else:
                newkey = urllib.parse.quote(keyword+' '+'RRR')
        else:
            newkey = urllib.parse.quote(keyword+' '+collection_num)
        return newkey
