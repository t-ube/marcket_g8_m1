import pandas as pd
import os
import datetime
import copy
from scripts import marcketPrice

class calc():
    def __init__(self, _date):
        self._date = _date

    def getBaseDf(self, _data_dir):
        files = os.listdir(_data_dir)
        files_file = [f for f in files if os.path.isfile(os.path.join(_data_dir, f)) and '.csv' in f]
        dfWrite = pd.DataFrame(index=[], columns=['market','link','price','name','date','datetime','stock'])
        dict_tmp = {}
        counter = 0
        for item in files_file:
            if os.path.getsize(_data_dir + '/' + item) < 10:
                continue
            readDf = pd.read_csv(
                _data_dir + '/' + item,
                encoding="utf_8_sig", sep=",",
                header=0)
            readDf['date'] = readDf['date'] + ' 00:00:00'
            if 'stock' not in readDf:
                readDf['stock'] = 0
            for index, row in readDf.iterrows():
                #print(row)
                newRow = copy.deepcopy(row)
                newRow['stock'] = 1
                #print(row['stock'])
                for i in range(row['stock']):
                    dict_tmp[counter] = newRow
                    counter += 1
                    #print(i)
                    #dfWrite = dfWrite.append(newRow)
            #df = pd.concat([df, dfWrite], ignore_index=True,axis=0,sort=False)
        dfWrite = dfWrite.from_dict(dict_tmp, orient="index")
        return dfWrite

    def getDailyDf(self,baseDf,days):
        tdatetime = datetime.datetime.strptime(self._date, '%Y-%m-%d')
        dateDf = pd.DataFrame(index=pd.date_range(end=tdatetime.strftime('%Y-%m-%d'), periods=days, freq="D"))
        dfInit = pd.DataFrame(index=dateDf.index, columns=['min', 'max', 'sum', 'mean', 'median', 'std', 'count'])
        if len(baseDf) == 0:
            return dfInit
        baseDf['date'] = pd.to_datetime(baseDf['date'])
        baseDf['price'] = baseDf['price'].astype(int)
        baseDf = baseDf[baseDf['stock'] > 0]
        if len(baseDf) == 0:
            return dfInit
        #calcDf = baseDf[['date','price']].groupby('date').agg(['min', 'max', 'sum', 'mean', 'median', 'std', 'count'])
        calcDf = baseDf[['date','price']].groupby('date').describe()
        df = calcDf.merge(dateDf, how="right", left_index=True, right_index=True)
        return df['price']

    def checkUpdate(self,_file,spanHours):
        io = marcketPrice.priceIO(_file)
        io.load()
        if io.checkUpdate(spanHours) is True:
            return True
        return False

    def writeDailyDf(self,
        _file,
        currentDf,
        d7Df,
        archiveWeekDf,
        diffWeekDf,
        archiveHalfYearDf,
        diffHalfYearDf):
        io = marcketPrice.priceIO(_file)
        for index, priceData in currentDf.iterrows():
            pd = marcketPrice.priceDaily()
            pd.setDateTime(index)
            pd.setDescribeData(priceData)
            if pd.isDescribeData(priceData):
                io.setCurrent(pd)
        for index, priceData in d7Df.iterrows():
            pd = marcketPrice.priceDaily()
            pd.setDateTime(index)
            pd.setDescribeData(priceData)
            io.set7DSummary(pd)
        for index, priceData in archiveWeekDf.iterrows():
            pd = marcketPrice.priceDaily()
            pd.setDateTime(index)
            pd.setDescribeData(priceData)
            io.addWeeklyArchive(pd)
        for index, priceData in diffWeekDf.iterrows():
            pd = marcketPrice.priceDaily()
            pd.setDateTime(index)
            pd.setDescribeData(priceData)
            io.addWeeklyDiff(pd)
        for index, priceData in archiveHalfYearDf.iterrows():
            pd = marcketPrice.priceDaily()
            pd.setDateTime(index)
            pd.setDescribeData(priceData)
            io.addHalfYearArchive(pd)
        for index, priceData in diffHalfYearDf.iterrows():
            pd = marcketPrice.priceDaily()
            pd.setDateTime(index)
            pd.setDescribeData(priceData)
            io.addHalfYearDiff(pd)
        io.save()
