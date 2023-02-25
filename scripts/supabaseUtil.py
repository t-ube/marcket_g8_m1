import os
import httpx
import numpy as np
import postgrest
import datetime
import pandas as pd
from supabase import create_client, Client 
from scripts import marcketPrice

# 一括処理用
class batchEditor:
    # card_market_raw 用の情報を生成する
    def getCardMarketRaw(self,master_id:str,raw):
        batch_item = {
            "master_id": master_id,
            "raw": raw
        }
        return batch_item

    # card_market_result 用の情報を生成する
    def getCardMarketResult(self,master_id:str,price):
        daily = marcketPrice.priceDaily()
        
        daily.setDescribeData(price['current'])
        if daily.validate() == False:
            print('Validation alert:'+master_id)
            daily.inf2zero()
            price['summary7Days'] = daily.get()

        daily.setDescribeData(price['summary7Days'])
        if daily.validate() == False:
            print('Validation alert:'+master_id)
            daily.inf2zero()
            price['summary7Days'] = daily.get()

        vol = marcketPrice.priceVolatility()

        vol.set(price['volatility'])
        if vol.validate() == False:
            print('Validation alert :'+master_id)
            vol.inf2zero()
            price['volatility'] = vol.get()

        timestamp = datetime.datetime.utcnow()
        batch_item = {
            "master_id": master_id,
            "updated_at": timestamp.strftime('%Y-%m-%d %H:%M:%S+00'),
            "calculated_at": timestamp.strftime('%Y-%m-%d %H:%M:%S+00'),
            "card_price": price
        }
        return batch_item

    # card_market_log 用の情報を生成する
    def getCardMarketLog(self,master_id:str,log):
        timestamp = datetime.datetime.utcnow()
        batch_item = {
            "master_id": master_id,
            "updated_at": timestamp.strftime('%Y-%m-%d %H:%M:%S+00'),
            "log": log
        }
        return batch_item

    # shop_item 用の情報を生成する
    def getShopItem(self,master_id:str, records):
        items = []
        if len(records) <= 0:
            return items
        timestamp = datetime.datetime.utcnow()
        for item in records:
            batch_item = {
                "master_id": master_id,
                "updated_at": timestamp.strftime('%Y-%m-%d %H:%M:%S+00'),
                "date": item['date'],
                "datetime": item['datetime']+'+09',
                "link": item['link'],
                "shop_name": item['market'],
                "item_name": item['name'],
                "price": item['price'],
                "stock": item['stock']
            }
            items.append(batch_item)
        return items

    def isNoneOrNan(self,data):
        if data == None:
            return True
        elif np.isnan(data):
            return True
        return False

    # card_price_daily 用の情報を生成する
    def getPriceDaily(self,master_id:str, records):
        items = []
        if len(records) <= 0:
            return items
        timestamp = datetime.datetime.utcnow()
        for item in records:
            batch_item = {
                "master_id": master_id,
                "updated_at": timestamp.strftime('%Y-%m-%d %H:%M:%S+00'),
                "datetime": item['datetime']+'+09',
                "count": int(item['count'])
            }

            if self.isNoneOrNan(item['mean']): batch_item["mean"] = None
            else : batch_item["mean"] = item['mean']
            if self.isNoneOrNan(item['std']): batch_item["std"] = None
            else : batch_item["std"] = item['std']
            if self.isNoneOrNan(item['min']): batch_item["min"] = None
            else : batch_item["min"] = item['min']
            if self.isNoneOrNan(item['25%']): batch_item["percent_25"] = None
            else : batch_item["percent_25"] = item['25%']
            if self.isNoneOrNan(item['50%']): batch_item["percent_50"] = None
            else : batch_item["percent_50"] = item['50%']
            if self.isNoneOrNan(item['75%']): batch_item["percent_75"] = None
            else : batch_item["percent_75"] = item['75%']
            if self.isNoneOrNan(item['max']): batch_item["max"] = None
            else : batch_item["max"] = item['max']

            items.append(batch_item)
        return items


# 一括書き込み用
class batchWriter:
    def write(self, supabase:Client, table_name:str, batch_item):
        if len(batch_item) <= 0:
            return True
        try:
            supabase.table(table_name).upsert(batch_item).execute()
            return True
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except httpx.WriteTimeout as e:
            print("httpx.WriteTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
            print('Begin error data')
            print(batch_item)
            print('End error data')
        return False

# card_market_raw の読み取り用
class marketRawReader:
    def read(self, supabase:Client, id_list):
        try:
            data = supabase.table("card_market_raw").select("master_id,id,created_at,raw").in_("master_id",id_list).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

# shop_item の読み取り用
class shopItemReader:
    def read(self, supabase:Client, id_list):
        try:
            data = supabase.table("shop_item_jst").select("master_id,id,datetime_jst,link,created_at,date,shop_name,item_name,price,stock").in_("master_id",id_list).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

# card_price_daily の読み取り用
class CardPriceDailyReader:
    def read(self, supabase:Client, id_list):
        try:
            data = supabase.table("card_price_daily_jst").select(
                "master_id,datetime_jst,created_at,updated_at,count,mean,std,min,percent_25,percent_50,percent_75,max"
                ).in_("master_id",id_list).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

    def readLimit(self, supabase:Client, id_list, base_date):
        try:
            data = supabase.table("card_price_daily_jst").select(
                "master_id,datetime_jst,created_at,updated_at,count,mean,std,min,percent_25,percent_50,percent_75,max"
                ).in_("master_id",id_list).limit(1000).order("datetime_jst", desc=True).gte("datetime_jst",self.limit(base_date, 30)).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

    def limit(self,base_date,days):
        td = datetime.timedelta(days=days)
        limit_date = base_date - td
        return limit_date.strftime('%Y-%m-%d 00:00:00')
    

# card_market_raw_updated_index の読み取り用
class marketRawUpdatedIndexReader:
    def read(self, supabase:Client):
        try:
            data = supabase.table("card_market_raw_updated_index").select("master_id_list").execute()
            if len(data.data) == 0:
                return []
            if data.data[0]['master_id_list'] == None:
                return []
            return data.data[0]['master_id_list'].split(',')
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []
    def readEx(self, supabase:Client):
        try:
            data = supabase.table("kinkyu_card_market_raw_updated_index").select("master_id_list").execute()
            if len(data.data) == 0:
                return []
            if data.data[0]['master_id_list'] == None:
                return []
            return data.data[0]['master_id_list'].split(',')
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

# card_market_raw の削除用
class marketRawCleaner:
    def delete(self, supabase:Client, id_list):
        try:
            data = supabase.table("card_market_raw").delete().in_("master_id",id_list).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

# shop_item の削除用
class shopItemCleaner:
    def limit(self,base_date):
        td = datetime.timedelta(days=8)
        limit_date = base_date - td
        return limit_date.strftime('%Y-%m-%d 00:00:00')

    def delete(self, supabase:Client, id_list, base_date):
        try:
            data = supabase.table("shop_item").delete().in_("master_id",id_list).lt("datetime",self.limit(base_date)).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []
