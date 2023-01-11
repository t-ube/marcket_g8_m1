import os
import httpx
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

# 一括書き込み用
class batchWriter:
    def write(self, supabase:Client, table_name:str, batch_item):
        try:
            supabase.table(table_name).upsert(batch_item).execute()
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except httpx.WriteTimeout as e:
            print("httpx.WriteTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)

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

# card_market_raw_updated_index の読み取り用
class marketRawUpdatedIndexReader:
    def read(self, supabase:Client):
        try:
            data = supabase.table("card_market_raw_updated_index").select("master_id_list").execute()
            if len(data.data) == 0:
                return []
            if data.data[0]['master_id_list'] == None:
                return []
            return data.data[0]['master_id_list']
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