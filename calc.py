import socket
import pandas as pd
from pathlib import Path
import os
import expansion
from scripts import jst
from scripts import marcketCalc
from scripts import marcketPrice

# 半年分のデータを取得する。（2週間間隔）
def getHalfYearData(ioCsv):
    d180Df = ioCsv.getDataframe().tail(180)
    d180Df = d180Df.replace(0, {'count': None})
    fillDf = d180Df.interpolate('ffill').interpolate('bfill')
    formatDf = fillDf.asfreq('14D', method='ffill')
    print(formatDf)
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
            daysDf = ioCsv.getDataframe().tail(7)
            daysDf = daysDf.replace(0, {'count': None})
            fillDf = daysDf.interpolate('ffill').interpolate('bfill')
            halfYearDf = getHalfYearData(ioCsv)
            # 最初と最後を抽出する
            sampleDf = pd.concat([fillDf.head(1), fillDf.tail(1)])
            calc.writeDailyDf(
                file,
                fillDf.tail(1),
                sampleDf.diff().tail(1),
                daysDf,
                fillDf.diff(),
                halfYearDf,
                halfYearDf.diff())
            backup.backup(1)
            backup.delete(2)
