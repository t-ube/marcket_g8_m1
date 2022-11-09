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
import math
import sys
import datetime
import re
from . import jst
from . import seleniumDriverWrapper as wrap
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import traceback

class magiListParser():
    def __init__(self, _html):
        self.__html = _html
        self.__reject = ['デッキ','ケース','募集','専用','様','プレイマット', 'スリーブ', '未開封', '予約', '構築', 'オリパ', 'パック', '管理', '買い取り', '買取', '注文用', '送料']
        #(ミラー)/

    def getItemList(self,keyword):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        aList = soup.find_all("a", class_="item-list__link")
        if aList is None:
            return l
        for a in aList:
            name = self.getItemName(a)
            if name is None:
                continue
            find = False
            for reject in self.__reject:
                if reject in name:
                    if reject == '様' and '仕様' in name:
                        continue
                    else:
                        find = True
                        break
            if find == False and self.keywordInName(keyword,name) and self.getSoldIcon(a) == False:
                price = int(self.getPrice(a).replace("¥ ","").replace(",","").replace(" ",""))
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
                l.append({
                    "market": 'magi',
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
        new_key = keyword.replace('　',' ').replace(' ','').replace('（','').replace('）','').replace('[','').replace(']','')
        new_name = name.replace('　',' ').replace(' ','').replace('（','').replace('）','').replace('[','').replace(']','')
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
    
    def getPrice(self,_BeautifulSoup):
        li = _BeautifulSoup.find("li", class_="item-list__price-box--price")
        if li is not None:
            return li.get_text()
        return None
    
    def getItemName(self,_BeautifulSoup):
        div = _BeautifulSoup.find("div", class_="item-list__item-name")
        if div is not None:
            return div.get_text()
        return None

    def getSoldIcon(self,_BeautifulSoup):
        div = _BeautifulSoup.find("div", class_="item-list__sold-icon")
        if div is not None:
            return True
        return False

    def getImage(self,_BeautifulSoup):
        img = _BeautifulSoup.find("img", class_="lozad lazyload lazyload--wrap")
        if img is not None:
            return img['data-src']
        return None

class magiDetailParser():
    def __init__(self, _html):
        self.__html = _html
        self.data = {
            "sku" : None,
            "brand_id" : None,
            "created_at" : None,
            "updated_by_owner_at": None,
            "price" : None,
            "priceCurrency": None,
            "availability": None,
        }

    def parse(self):
        soup = BeautifulSoup(self.__html, 'html.parser')
        self.parseA(soup)
        self.parseB(soup)
        return self.data

    def parseA(self,soup):
        scripts = soup.find_all("script")
        for script in scripts:
            if 'created_at' in script.get_text():
                txtList = str(script).split("item: {")
                for txt in txtList:
                    txtList2 = str(txt).split("},")
                    for txt2 in txtList2:
                        if 'created_at' in txt2:
                            text = txt2.replace('\r\n','').replace('\n','')
                            json_object = json.loads('{'+text+'}')
                            self.data["brand_id"] = self.getBrandId(json_object)
                            self.data["created_at"] = self.getCreatedAt(json_object)
                            self.data["updated_by_owner_at"] = self.getUpdatedAt(json_object)
                            self.data["price"] = self.getPrice(json_object)

    def parseB(self,soup):
        script = soup.find("script", type="application/ld+json")
        text = script.get_text().replace('\r\n','').replace('\n','')
        json_object = json.loads(text)
        self.data["sku"] = self.getSku(json_object)
        self.data["priceCurrency"] = self.getPriceCurrency(json_object)
        self.data["availability"] = self.getAvailability(json_object)

    def getBrandId(self,json):
        if 'brand_id' in json:
            return json['brand_id']
        return None

    def getCreatedAt(self,json):
        if 'created_at' in json:
            return json['created_at']
        return None

    def getUpdatedAt(self,json):
        if 'updated_by_owner_at' in json:
            return json['updated_by_owner_at']
        return None

    def getPrice(self,json):
        if 'price' in json:
            return json['price']
        return None

    def getSku(self,json):
        if 'sku' in json:
            return json['sku']
        return None

    def getPriceCurrency(self,json):
        if 'offers' in json:
            if 'priceCurrency' in json['offers']:
                return json['offers']['priceCurrency']
        return None

    def getAvailability(self,json):
        if 'offers' in json:
            if 'availability' in json['offers']:
                return json['offers']['availability']
        return None

class magiCsvRecord():
    def __init__(self):
        self.data = {
            "link": None,
            "price": None,
            "name": None,
            "image": None,
            "sku" : None,
            "brand_id" : None,
            "created_at" : None,
            "updated_by_owner_at": None,
            "priceCurrency": None,
            "availability": None,
        }

    def merge(self,header,data):
        self.data['link'] = header['link']
        self.data['name'] = header['name']
        self.data['image'] = header['image']
        self.data['sku'] = data['sku']
        self.data['brand_id'] = data['brand_id']
        self.data['created_at'] = data['created_at']
        self.data['updated_by_owner_at'] = data['updated_by_owner_at']
        self.data['price'] = data['price']
        self.data['priceCurrency'] = data['priceCurrency']
        self.data['availability'] = data['availability']
        return self.data

class magiCsv():
    def __init__(self,_src):
        self.__file = _src
        self.__df = None

    def load(self):
        if os.path.isfile(self.__file) == False:
            self.init()
        labels = ['link', 'price', 'name', 'image', 'sku', 'brand_id', 'created_at', 'updated_by_owner_at', 'priceCurrency', 'availability']
        self.__df = pd.read_csv(self.__file,names=labels, header=0)

    def init(self):
        labels = ['link', 'price', 'name', 'image', 'sku', 'brand_id', 'created_at', 'updated_by_owner_at', 'priceCurrency', 'availability']
        try:
            with open(self.__file, 'w', newline="", encoding="utf_8_sig") as f:
                writer = csv.DictWriter(f, fieldnames=labels)
                writer.writeheader()
                f.close()
        except IOError:
            print("I/O error")

    def isLink(self, link):
        newDf = self.__df[self.__df['link'] == link]
        if len(newDf) > 0 :
            return True
        return False

    def add(self, header, data):
        record = magiCsvRecord()
        record.merge(header,data)
        l = list()
        l.append(record.data)
        self.__df = pd.concat([self.__df, pd.DataFrame.from_dict(l)])
        #self.__df.append(pd.Series(record.data), ignore_index=True)

    def save(self):
        if os.path.isfile(self.__file) == False:
            self.init()
            self.load()
        self.__df.to_csv(self.__file, index=False, encoding='utf_8_sig')

class magiSearchCsv():
    def __init__(self,_out_dir):
        dt = jst.now().replace(microsecond=0)
        self.__out_dir = _out_dir
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_magi.csv'

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

class magiCsvBot():
    def download(self, drvWrapper, first_page, keyword, expansion, collection_num, rarity, out_dir):
        # カード一覧へ移動
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        csv = magiSearchCsv(out_dir)

        new_keylist = self.getNewKey(keyword,expansion,collection_num,rarity)
        for new_key in new_keylist:
            nextLoop = True
            page_number = first_page - 1
            while nextLoop:
                page_number += 1
                print('---------------')
                print(page_number)
                print('---------------')
                self.getResultPageB(drvWrapper.getDriver(), new_key, page_number)

                try:
                    drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'item-list__container')))
                    #time.sleep(1)
                    listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
                    parser = magiListParser(listHtml)
                    l = parser.getItemList(keyword)
                    if len(l) == 0:
                        break
                    for item in l:
                        csv.add(item)
                        print(item)
                except TimeoutException as e:
                    print("TimeoutException")
                except Exception as e:
                    print(traceback.format_exc())
        csv.save()

    def getCardFileName(self, data_src):
        basename_without_ext = os.path.splitext(os.path.basename(data_src))[0]
        return basename_without_ext

    def getResultPageNormal(self, driver, keyword, page_number):
        url = 'https://magi.camp/items/search?forms_search_items%5Bkeyword%5D='+keyword
        if page_number > 1:
            url += '&page=' + str(page_number)
        driver.get(url)

    def getResultPageA(self, driver, keyword, page_number):
        url = 'https://magi.camp/items/search?forms_search_items%5Bkeyword%5D='+keyword
        url += '&forms_search_items%5Bgoods_id%5D=1'
        url += '&forms_search_items%5Bbrand_id%5D=3'
        url += '&forms_search_items%5Bseries_id%5D=31'
        url += '&item%5Bcustom_attributes%5D%5B0%5D%5Bname%5D=size'
        url += '&item%5Bcustom_attributes%5D%5B0%5D%5Bvalues%5D%5B%5D='
        url += '&forms_search_items%5Bfrom_price%5D='
        url += '&forms_search_items%5Bto_price%5D='
        url += '&forms_search_items%5Bstatus%5D=presented'
        url += '&forms_search_items%5Bsort%5D='
        url += '&forms_search_items%5Bpage%5D='+ str(page_number)
        url += '&commit=検索する'
        print(url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())

    def getResultPageB(self, driver, keyword, page_number):
        url = 'https://magi.camp/items/search?'
        url += '&forms_search_items%5Bbrand_id%5D=3'
        url += '&forms_search_items%5Bfrom_price%5D='
        url += '&forms_search_items%5Bgoods_id%5D=1'
        url += '&forms_search_items%5Bkeyword%5D='+keyword
        url += '&forms_search_items%5Bseries_id%5D=31'
        url += '&forms_search_items%5Bsort%5D='
        url += '&forms_search_items%5Bstatus%5D=presented'
        url += '&forms_search_items%5Bto_price%5D='
        url += '&item%5Bcustom_attributes%5D%5B0%5D%5Bname%5D=size'
        url += '&item%5Bcustom_attributes%5D%5B0%5D%5Bvalues%5D%5B%5D='
        url += '&page='+ str(page_number)
        print(url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())

    def getDetailPage(self, driver, link):
        url = 'https://magi.camp'+link
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())

    def getNewKey(self, keyword, expansion, collection_num, rarity):
        keylist = []
        temp = keyword.replace('　',' ').replace('（',' ').replace('）',' ')
        if 'V-UNION' in temp and 'モルペコ' in temp:
            if '226' in collection_num or '227' in collection_num or '228' in collection_num or '229' in collection_num:
                newkey = urllib.parse.quote(temp+'　'+'CSR')
            else:
                newkey = urllib.parse.quote(temp+'　'+'RRR')
        else:
            newkey = urllib.parse.quote(temp+'　'+collection_num)
        keylist.append(newkey)

        if rarity == 'A' and (expansion == 'S3a' or expansion == 'S4a'):
            newkey = urllib.parse.quote(temp+'　'+'アメイジング')
            keylist.append(newkey)

        if keyword == 'ブースターVMAX' and collection_num == '186/S-P':
            newkey = urllib.parse.quote(temp+'　'+'夏ポ')
            keylist.append(newkey)
        if keyword == 'シャワーズVMAX' and collection_num == '187/S-P':
            newkey = urllib.parse.quote(temp+'　'+'夏ポ')
            keylist.append(newkey)
        if keyword == 'サンダースVMAX' and collection_num == '188/S-P':
            newkey = urllib.parse.quote(temp+'　'+'夏ポ')
            keylist.append(newkey)

        return keylist
