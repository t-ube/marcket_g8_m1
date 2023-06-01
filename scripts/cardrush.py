from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import csv
import os
import datetime
import re
from . import jst
from . import seleniumDriverWrapper as wrap
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import traceback

class cardrushListParser():
    def __init__(self, _html):
        self.__html = _html
        self.__reject = ['デッキ','ケース','プレイマット','スリーブ']
        #(ミラー)

    def getItemList(self,keyword):
        soup = BeautifulSoup(self.__html, 'html.parser')
        l = list()
        liList = soup.find_all("li", class_="list_item_cell")
        for li in liList:
            name = self.getItemNameV2(li)
            if name is None:
                continue
            find = False
            for reject in self.__reject:
                if reject in name:
                    find = True
                    break
            if find == False and self.keywordInName(keyword,name):
                if self.getPrice(li) == None:
                    continue
                l.append({
                    "market": 'cardrush',
                    "link": self.getLink(li),
                    "price": int(re.findall('[0-9]+', self.getPrice(li).replace(',',''))[0]),
                    "name": '{:.10}'.format(name),
                    #"image": self.getImage(a),
                    "date": None,
                    "datetime": None,
                    "stock": self.getStock(li),
                })
        return l

    def keywordInName(self,keyword,name):
        if keyword in name:
            return True
        new_name = name.replace('　',' ').replace(' ','').replace('（','').replace('）','').replace('/','')
        new_key = keyword.replace('　',' ').replace('（',' ').replace('）',' ').replace('/',' ')
        new_key_l = new_key.split(' ')
        for key in new_key_l:
            if key is not None and len(key) > 0 and key not in new_name:
                return False
        return True
    
    def getPrice(self,_BeautifulSoup):
        span = _BeautifulSoup.find("span", class_="figure")
        if span is not None:
            return span.get_text()
        return None

    def getItemNameV2(self,_BeautifulSoup):
        p = _BeautifulSoup.find("span", class_="goods_name")
        if p == None:
            return None
        text = ''
        text = p.get_text()
        return text
    
    def getItemName(self,_BeautifulSoup):
        spanParent = _BeautifulSoup.find("span", class_="goods_name")
        if spanParent == None:
            return None
        spanChileds = spanParent.find_all("span")
        if spanChileds == None or len(spanChileds) == 0:
            return None
        text = ''
        for span in spanChileds:
            if span is not None:
                b = span.find("b")
                if b is not None:
                    text += b.get_text()
        return text

    def getLink(self,_BeautifulSoup):
        a = _BeautifulSoup.find("a", class_="item_data_link")
        if a is not None:
            if a.has_attr('href'):
                return a['href']
        return None

    def getImage(self,_BeautifulSoup):
        div = _BeautifulSoup.find("div", class_="global_photo")
        if div is not None:
            img = _BeautifulSoup.find("img")
            if img is not None:
                if img.has_attr('src'):
                    return img['src']
        return None
    
    def getStock(self,_BeautifulSoup):
        a = _BeautifulSoup.find("a", class_="item_data_link")
        if a is not None:
            p = a.find("p", class_="stock")
            if p is not None:
                find_pattern = r"(?P<c>[0-9,]+)"
                m = re.search(find_pattern, p.get_text())
                if m != None:
                    return int(m.group('c').replace(',',''))
        return 0

class cardrushSearchCsv():
    def __init__(self,_out_dir):
        dt = jst.now().replace(microsecond=0)
        self.__out_dir = _out_dir
        self.__list = list()
        self.__date = str(dt.date())
        self.__datetime = str(dt)
        self.__file = _out_dir+'/'+self.__datetime.replace("-","_").replace(":","_").replace(" ","_")+'_cardrush.csv'

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
        df = pd.DataFrame.from_dict(self.__list)
        if os.path.isfile(self.__file) == False:
            self.init()
        df.to_csv(self.__file, index=False, encoding='utf_8_sig')

class cardrushCsvBot():
    def download(self, drvWrapper, keyword, collection_num, out_dir):
        # カード一覧へ移動
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        searchCsv = cardrushSearchCsv(out_dir)

        new_key = keyword.replace('　',' ').replace('（',' ').replace('）',' ')
        self.getResultPageNormal(drvWrapper.getDriver(), new_key+' '+collection_num)

        try:
            drvWrapper.getWait().until(EC.visibility_of_all_elements_located((By.CLASS_NAME,'itemlist_box')))
            #time.sleep(3)
            listHtml = drvWrapper.getDriver().page_source.encode('utf-8')
            parser = cardrushListParser(listHtml)
            l = parser.getItemList(keyword)
            for item in l:
                searchCsv.add(item)
                print(item)
            searchCsv.save()
        except TimeoutException as e:
            print("TimeoutException")
        except Exception as e:
            print(traceback.format_exc())
        
    def getResultPageNormal(self, driver, keyword):
        url = 'https://www.cardrush-pokemon.jp/product-list?num=100&img=120&order=rank&keyword='+keyword
        url += '&Submit=%E6%A4%9C%E7%B4%A2'
        print(url)
        try:
            driver.get(url)
        except WebDriverException as e:
            print("WebDriverException")
        except Exception as e:
            print(traceback.format_exc())
