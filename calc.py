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


# 1週間分のデータを取得する。
def getWeeklyData(ioCsv, currentDT):
    firstDate = currentDT - datetime.timedelta(days=7)
    rangeDf = pd.DataFrame(index=pd.date_range(
        firstDate.strftime('%Y-%m-%d'),
        currentDT.strftime('%Y-%m-%d')))
    dfCsv = ioCsv.getDataframe()
    d7Df = pd.merge(rangeDf,dfCsv,how='outer',left_index=True,right_index=True)
    d7Df = d7Df.replace(0, {'count': None})
    fillDf = d7Df.interpolate('ffill')
    formatDf = fillDf.asfreq('1D', method='ffill').fillna(0).tail(7)
    #print(formatDf)
    return formatDf

# 半年分のデータを取得する。（2週間間隔）
def getHalfYearData(ioCsv, currentDT):
    firstDate = currentDT - datetime.timedelta(days=168)
    rangeDf = pd.DataFrame(index=pd.date_range(
        firstDate.strftime('%Y-%m-%d'),
        currentDT.strftime('%Y-%m-%d')))
    dfCsv = ioCsv.getDataframe()
    d168Df = pd.merge(rangeDf,dfCsv,how='outer',left_index=True,right_index=True)
    d168Df = d168Df.replace(0, {'count': None})
    fillDf = d168Df.interpolate('ffill')
    formatDf = fillDf.asfreq('14D', method='ffill').fillna(0)
    #print(formatDf)
    return formatDf


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

rawReader = supabaseUtil.marketRawReader()
editor = supabaseUtil.batchEditor()
writer = supabaseUtil.batchWriter()
cleaner = supabaseUtil.marketRawCleaner()

currentDT = jst.now()
print(currentDT)

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
        data = rawReader.read(supabase,batch)
        if len(data) > 0:
            batch_logs = []
            batch_results = []
            df = pd.DataFrame.from_records(data)
            for master_id in batch:
                cardDf = df[df['master_id'] == master_id]
                records = []
                for index, row in cardDf.iterrows():
                    records.extend(row['raw'])
                recordDf = pd.DataFrame.from_records(records)
                print(master_id)
                if len(records) > 0:
                    recordDf = recordDf.sort_values(by=['datetime'], ascending=False) 
                    recordDf = recordDf[~recordDf.duplicated(subset=['market','date','name','link'],keep='first')]
                #print(recordDf)
                dataDir = './data/marcket/'+master_id
                if os.path.exists(dataDir) == False:
                    Path(dataDir).mkdir(parents=True, exist_ok=True)

                # ログ（CSVとSupabaseに記録する）
                log_file = './log/'+row['master_id']+'.json'
                log = marcketPrice.priceLogCsv(dataDir)
                log.save(recordDf, currentDT.strftime('%Y-%m-%d'))
                log.convert2Json(log_file)
                batch_logs.append(editor.getCardMarketLog(master_id,log.getList()))

                # 日次情報（CSVに記録する）
                dailyCsv = marcketPrice.dailyPriceIOCSV(dataDir)
                dailyCsv.load()
                calc = marcketCalc.calc(currentDT.strftime('%Y-%m-%d'))
                recordDf = calc.convert2BaseDf(recordDf)
                days30Df = calc.getDailyDf2(recordDf,30)
                dailyCsv.add(days30Df)
                #print(dailyCsv.getDict())
                dailyCsv.save()

                # 集計結果（CSVとSupabaseに記録する）
                # 1週間分のデータを取得する。（日間）
                daysDf = getWeeklyData(dailyCsv, currentDT)
                halfYearDf = getHalfYearData(dailyCsv, currentDT)
                # 最初と最後を抽出する
                sampleDf = pd.concat([daysDf.head(1), daysDf.tail(1)])
                batch_results.append(editor.getCardMarketResult(master_id,
                    calc.getWriteDailyDf(
                    None,
                    daysDf.tail(1),
                    sampleDf.diff().tail(1),
                    daysDf,
                    daysDf.diff(),
                    halfYearDf,
                    halfYearDf.diff())
                ))
                file = './dist/'+row['master_id']+'.json'
                calc.writeDailyDf(
                    file,
                    daysDf.tail(1),
                    sampleDf.diff().tail(1),
                    daysDf,
                    daysDf.diff(),
                    halfYearDf,
                    halfYearDf.diff())
                # バックアップ
                backup = marcketPrice.backupPriceRawCSV(dataDir)
                backup.backup(1)
                backup.delete(1)
            #print(batch_results)
            #print(batch_logs)
            writer.write(supabase, "card_market_result", batch_results)
            writer.write(supabase, "card_market_log", batch_logs)
            # 削除
            cleaner.delete(supabase,batch)
