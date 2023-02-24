import os
from get_chrome_driver import GetChromeDriver
from selenium import webdriver
import socket
import time
import pandas as pd
from pathlib import Path
import expansion
from supabase import create_client, Client 
from scripts import seleniumDriverWrapper as wrap
from scripts import cardrush
from scripts import hareruya2
from scripts import magi
from scripts import torecolo
from scripts import marcketConfig
from scripts import marcketCalc
from scripts import supabaseUtil

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

get_driver = GetChromeDriver()
get_driver.install()

wrapper = wrap.seleniumDriverWrapper()
wrapper.begin(webdriver)
cardrushBot = cardrush.cardrushCsvBot()
hareruya2Bot = hareruya2.hareruya2CsvBot()
magiBot = magi.magiCsvBot()
torecoloBot = torecolo.torecoloCsvBot()

ip = socket.gethostbyname(socket.gethostname())
print(ip)

start = time.time()
loader = marcketCalc.rawLoader()
writer = supabaseUtil.batchWriter()
editor = supabaseUtil.batchEditor()
reader = supabaseUtil.marketRawUpdatedIndexReader()
updated_id_list = reader.read(supabase)

counter = 0

# バッチは10件溜まったらPOSTして空にする
batch_items = []
batch_master_id = []

for exp in expansion.getList():
    print('check:'+exp)
    dfExp = pd.read_csv('./data/card/'+exp+'.csv', header=0, encoding='utf_8_sig')
    if time.time() - start > 480:
        break

    for index, row in dfExp.iterrows():
        if time.time() - start > 480:
            break
        if pd.isnull(row['master_id']):
            print('skip:'+row['name'])
            continue
        if row['is_mirror'] == 'TRUE':
            print('skip:'+row['name']+' '+row['master_id'])
            continue
        if row['master_id'] in updated_id_list:
            print('skip:'+row['name']+' '+row['master_id'])
            continue
        # CSVのマスタIDが重複する可能性がある
        if row['master_id'] in batch_master_id:
            print('skip (already exist):'+row['name']+' '+row['master_id'])
            continue

        dataDir = './data/marcket/'+row['master_id']
        torecoloBot.download(wrapper, row['name'], row['cn'], dataDir)
        cardrushBot.download(wrapper, row['name'], row['cn'], dataDir)
        hareruya2Bot.download(wrapper, row['name'], row['cn'], dataDir)
        magiBot.download(wrapper, 1, row['name'], row['expansion'], row['cn'], row['rarity'], dataDir)

        df = loader.getUniqueRecodes(dataDir)
        records = df.to_dict(orient='records')
        items = editor.getShopItem(row['master_id'],records)
        if len(items) > 0:
            batch_items.extend(items)
            batch_master_id.append(row['master_id'])
            counter += 1

        if len(batch_items) >= 10:
            writer.write(supabase, "shop_item", batch_items)
            batch_items = []
            batch_master_id = []


# 残っていたらPOSTする
if len(batch_items) > 0:
    writer.write(supabase, "shop_item", batch_items)
    batch_items = []
    batch_master_id = []

print('count:'+str(counter))

wrapper.end()
