import os
import json
import httpx
import postgrest
import datetime
import time
import copy
import pandas as pd
import expansion
from pathlib import Path
from uuid import UUID
from supabase import create_client, Client 
from scripts import jst
from scripts import marcketCalc
from scripts import marcketPrice
from scripts import supabaseUtil


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

editor = supabaseUtil.batchEditor()
writer = supabaseUtil.batchWriter()

currentDT = jst.now()
print(currentDT)

if os.path.exists('./log') == False:
    Path('./log').mkdir(parents=True, exist_ok=True)

for exp in expansion.getList():
    print('check:'+exp)
    dfExp = pd.read_csv('./data/card/'+exp+'.csv', header=0, encoding='utf_8_sig')
    id_list = []
    for index, row in dfExp.iterrows():
        if pd.isnull(row['master_id']):
            print('skip:'+row['name'])
            continue
        id_list.append(row['master_id'])

    for i in range(0, len(id_list), 100):
        batch = id_list[i: i+100]
        print('Write log no.:'+str(i))
        # 日次記録をファイルに書き込む
        for master_id in batch:
            dataDir = './data/marcket/'+master_id
            if os.path.exists(dataDir) == False:
                Path(dataDir).mkdir(parents=True, exist_ok=True)
            dailyCsv = marcketPrice.dailyPriceIOCSV(dataDir)
            dailyCsv.load()
            records = dailyCsv.getMigrateData()
            if len(records) > 0:
                batch_results = editor.getPriceDaily(master_id, records)
                result1 = writer.write(supabase, "card_price_daily", batch_results)
                if result1 == True:
                    print('ファイル削除')
