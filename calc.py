import socket
import pandas as pd
from pathlib import Path
import os
import expansion
import datetime
from scripts import jst
from scripts import marcketCalc
from scripts import marcketPrice

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

ip = socket.gethostbyname(socket.gethostname())
print(ip)

currentDT = jst.now()
print(currentDT)

Path('./dist').mkdir(parents=True, exist_ok=True)
Path('./log').mkdir(parents=True, exist_ok=True)

for exp in expansion.getList():
    dfExp = pd.read_csv('./data/card/'+exp+'.csv', header=0, encoding='utf_8_sig')
    for index, row in dfExp.iterrows():
        if pd.isnull(row['master_id']):
            print('skip:'+row['name'])
            continue

        dataDir = './data/marcket/'+row['master_id']
        file = './dist/'+row['master_id']+'.json'
        log_file = './log/'+row['master_id']+'.jsonl'

        if os.path.exists(dataDir) == False:
            continue

        calc = marcketCalc.calc(currentDT.strftime('%Y-%m-%d'))
        if calc.checkUpdate(file, 4) is False:
            print('Already calculated')
        else:
            ioCsv = marcketPrice.dailyPriceIOCSV(dataDir)
            backup = marcketPrice.backupPriceRawCSV(dataDir)
            log = marcketPrice.priceLogCsv(dataDir)
            ioCsv.load()
            
            df = calc.getUniqueRecodes(dataDir)
            log.save(df, currentDT.strftime('%Y-%m-%d'))
            log.convert2JsonLines(log_file)

            df = calc.convert2BaseDf(df)
            days30Df = calc.getDailyDf(df,30)
            ioCsv.add(days30Df)
            ioCsv.save()

            # 1週間分のデータを取得する。（日間）
            daysDf = getWeeklyData(ioCsv, currentDT)
            halfYearDf = getHalfYearData(ioCsv, currentDT)
            # 最初と最後を抽出する
            sampleDf = pd.concat([daysDf.head(1), daysDf.tail(1)])
            calc.writeDailyDf(
                file,
                daysDf.tail(1),
                sampleDf.diff().tail(1),
                daysDf,
                daysDf.diff(),
                halfYearDf,
                halfYearDf.diff())
            backup.backup(1)
            backup.delete(1)
