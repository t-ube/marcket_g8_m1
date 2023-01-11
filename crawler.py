import os
from get_chrome_driver import GetChromeDriver
from selenium import webdriver
import socket
import time
import pandas as pd
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
updated_id_list = reader.readEx(supabase)

for exp in expansion.getList():
    print('check:'+exp)
    dfExp = pd.read_csv('./data/card/'+exp+'.csv', header=0, encoding='utf_8_sig')
    if time.time() - start > 480:
        break

    for index, row in dfExp.iterrows():
        batch_items = []
        if time.time() - start > 480:
            break
        if pd.isnull(row['master_id']):
            print('skip:'+row['name'])
            continue
        if row['is_mirror'] == 'TRUE':
            print('skip:'+row['name'])
            continue
        if row['master_id'] in updated_id_list:
            print('skip:'+row['name'])
            continue 

        dataDir = './data/marcket/'+row['master_id']
        torecoloBot.download(wrapper, row['name'], row['cn'], dataDir)
        cardrushBot.download(wrapper, row['name'], row['cn'], dataDir)
        hareruya2Bot.download(wrapper, row['name'], row['cn'], dataDir)
        magiBot.download(wrapper, 1, row['name'], row['expansion'], row['cn'], row['rarity'], dataDir)

        df = loader.getUniqueRecodes(dataDir)
        batch_items.append(editor.getCardMarketRaw(row['master_id'],df.to_dict(orient='records')))
        writer.write(supabase, "card_market_raw", batch_items)

wrapper.end()
