import os
import pandas as pd
import expansion
from supabase import create_client, Client 
from scripts import marcketCalc
from scripts import supabaseUtil

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

editor = supabaseUtil.batchEditor()
writer = supabaseUtil.batchWriter()

for exp in expansion.getList():
    print('check:'+exp)
    dfExp = pd.read_csv('./data/card/'+exp+'.csv', header=0, encoding='utf_8_sig')
    batch_items = []
    for index, row in dfExp.iterrows():
        if pd.isnull(row['master_id']):
            print('skip:'+row['name'])
            continue
        dataDir = './data/marcket/'+row['master_id']
        if os.path.exists(dataDir) == False:
            continue
        loader = marcketCalc.rawLoader()
        df = loader.getUniqueRecodes(dataDir)
        batch_items.append(editor.getCardMarketRaw(row['master_id'],df.to_dict(orient='records')))
    writer.write(supabase, "card_market_raw", batch_items)
