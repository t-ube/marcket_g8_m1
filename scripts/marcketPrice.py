import os
import json
import numpy as np
import pandas as pd
import datetime
import shutil
import re
from . import jst

# 価格データ
class priceDaily():
    def __init__(self):
        self.data = {
            "datetime": None,
            "count": None,
            "mean": None,
            "std": None,
            "min": None,
            "25%": None,
            "50%": None,
            "75%": None,
            "max": None
        }

    def isDescribeData(self,desc):
        if 'min' not in desc:
            return False
        if desc['min'] == None:
            return False
        if self.getValue(desc['min']) == None:
            return False
        return True

    def setDescribeData(self,desc):
        self.data['count'] = self.getValue(desc['count'])
        self.data['mean'] = self.getValue(desc['mean'])
        self.data['std'] = self.getValue(desc['std'])
        self.data['min'] = self.getValue(desc['min'])
        self.data['25%'] = self.getValue(desc['25%'])
        self.data['50%'] = self.getValue(desc['50%'])
        self.data['75%'] = self.getValue(desc['75%'])
        self.data['max'] = self.getValue(desc['max'])
    
    def setDateTime(self,datetime):
        tstr = datetime.strftime('%Y-%m-%d 00:00:00')
        self.data['datetime'] = tstr

    def getValue(self,value):
        if np.isnan(value):
            return None
        return value

# 価格データ
class priceVolatility():
    def __init__(self):
        self.data = {
            "weekly": None,
            "daily": None,
        }

    # 差分データの変化率を計算する
    def calcDailyData(self, df, colName):
        d2 = df.tail(2)
        dailyBase = 0.0
        daily = 0.0
        dailyCurrent = 0.0
        for index, data in d2.fillna(0).head(1).iterrows():
            dailyBase = data[colName]
        for index, data in d2.fillna(0).tail(1).iterrows():
            dailyCurrent = data[colName]
        for index, data in d2.pct_change().fillna(0).tail(1).iterrows():
            daily = data[colName]
        return {'basePrice': dailyBase, 'latestPrice': dailyCurrent, 'percent': round(daily*100, 2)}

    def getDailyData(self, df):
        return {
            'min': self.calcDailyData(df, 'min'),
            '50%': self.calcDailyData(df, '50%')
        }

    def calcWeeklyData(self, df, colName):
        d7 = pd.concat([df.head(1), df.tail(1)])
        weeklyBase = 0.0
        weekly = 0.0
        weeklyCurrent = 0.0
        for index, data in d7.fillna(0).head(1).iterrows():
            weeklyBase = data[colName]
        for index, data in d7.fillna(0).tail(1).iterrows():
            weeklyCurrent = data[colName]
        for index, data in d7.pct_change().fillna(0).tail(1).iterrows():
            weekly = data[colName]
        return {'basePrice': weeklyBase, 'latestPrice': weeklyCurrent, 'percent': round(weekly*100, 2)}

    def getWeeklyData(self, df):
        return {
            'min': self.calcWeeklyData(df, 'min'),
            '50%': self.calcWeeklyData(df, '50%')
        }

    def setWeeklyData(self,df):
        self.data['daily'] = self.getDailyData(df)
        self.data['weekly'] = self.getWeeklyData(df)

# 価格読み書き
class priceIO():
    def __init__(self, _file):
        self.__file = _file
        self.data = {
            "price": {
                "current": None,
                "summary7Days": None,
                "volatility": None,
                "weekly": {
                    "archive": {
                        "count": 0,
                        "data": []
                    },
                    "diff": {
                        "count": 0,
                        "data": []
                    }
                },
                "halfYear": {
                    "archive": {
                        "count": 0,
                        "data": []
                    },
                    "diff": {
                        "count": 0,
                        "data": []
                    }
                },
                "OneYear": {
                    "archive": {
                        "count": 0,
                        "data": []
                    },
                    "diff": {
                        "count": 0,
                        "data": []
                    }
                }
            },
            "calc": {
                "latest_date": None,
                "updated_at": None
            }
        }

    def load(self):
        if os.path.isfile(self.__file) == False:
            return
        with open(self.__file, encoding='utf_8_sig') as f:
            self.data = json.load(f)

    def checkUpdate(self, spanHours):
        current = jst.now().replace(microsecond=0)
        if 'calc' not in self.data:
            return True
        if 'updated_at' not in self.data['calc']:
            return True
        if self.data['calc']['updated_at'] is None:
            return True
        tdelta = datetime.timedelta(hours=spanHours)
        tdatetime = datetime.datetime.strptime(self.data['calc']['updated_at'], '%Y-%m-%d %H:%M:%S')
        if current > tdatetime + tdelta:
            return True
        return False

    def setCurrent(self,price:priceDaily):
        self.data['price']['current'] = price.data
        self.data['calc']['latest_date'] = price.data['datetime']

    def set7DSummary(self,price:priceDaily):
        self.data['price']['summary7Days'] = price.data
    
    def setPriceVolatility(self,price:priceVolatility):
        self.data['price']['volatility'] = price.data

    def addWeeklyArchive(self,price:priceDaily):
        self.addArchive('weekly', price)

    def addWeeklyDiff(self,price:priceDaily):
        self.addDiff('weekly', price)

    def addHalfYearArchive(self,price:priceDaily):
        self.addArchive('halfYear', price)

    def addHalfYearDiff(self,price:priceDaily):
        self.addDiff('halfYear', price)

    def addArchive(self,span,price:priceDaily):
        self.data['price'][span]['archive']['count'] += 1
        self.data['price'][span]['archive']['data'].append(price.data)

    def addDiff(self,span,price:priceDaily):
        self.data['price'][span]['diff']['count'] += 1
        self.data['price'][span]['diff']['data'].append(price.data)

    def save(self):
        self.data['calc']['updated_at'] = jst.now().strftime('%Y-%m-%d %H:%M:%S')
        #print(self.data)
        with open(self.__file, 'w') as f:
            json.dump(self.data, f, indent=4)

# 日次価格記録読み書き
class dailyPriceIOCSV():
    def __init__(self, data_dir):
        self.__data_dir = data_dir
        self.__calc_dir = self.__data_dir + '/calc'
        self.__calc_csv = self.__calc_dir + '/daily_price.csv'
        self.__df = pd.DataFrame(index=[],
        columns=['datetime','count','mean','std','min','25%','50%','75%','max'])
        self.__df.set_index('datetime')
        self.__df.index = pd.to_datetime(self.__df.index, format='%Y-%m-%d %H:%M:%S')

    def load(self):
        if os.path.isdir(self.__data_dir) is False:
            return
        if os.path.isdir(self.__calc_dir) is False:
            return
        if os.path.isfile(self.__calc_csv) is False:
            return
        if os.path.getsize(self.__calc_csv) < 10:
            return
        self.__df = pd.read_csv(
            self.__calc_csv,
            encoding="utf_8_sig", sep=",",
            index_col="datetime",
            header=0)
        self.__df.index = pd.to_datetime(self.__df.index, format='%Y-%m-%d %H:%M:%S')

    def save(self):
        if os.path.isdir(self.__data_dir) is False:
            return
        if os.path.isdir(self.__calc_dir) is False:
            os.mkdir(self.__calc_dir)
        self.__df.to_csv(self.__calc_csv,
            header=True,
            index=True,
            index_label='datetime',
            encoding='utf_8_sig',
            columns=['count','mean','std','min','25%','50%','75%','max'],
            date_format='%Y-%m-%d %H:%M:%S'
            )

    def add(self, df):
        df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')
        #df.set_index('datetime')
        self.__df = pd.concat([self.__df,df],axis=0)
        self.__df = self.__df.fillna({'count': 0})
        # 新しく重複かつ値がないものを削除
        self.__df = self.__df[~((self.__df.index.duplicated(keep='first')) & (self.__df['count'] == 0))]
        # その後、インデックスが重複した場合には古いデータを破棄する
        self.__df = self.__df[~self.__df.index.duplicated(keep='last')]
        self.__df = self.__df.sort_index()

    def getDataframe(self):
        return self.__df

# 日次経過ファイルをバックアップする
class backupPriceRawCSV():
    def __init__(self, data_dir):
        self.__data_dir = data_dir
        self.__raw_dir = self.__data_dir + '/backup'

    def getFileDate(self, file:str):
        find_pattern = r'(?P<Y>\d{4})_(?P<m>\d{2})_(?P<d>\d{2})_(?P<H>\d{2})_(?P<M>\d{2})_(?P<S>\d{2})'
        m = re.search(find_pattern, file)
        if m != None:
            time_str = m.group('Y')+'-'+m.group('m')+'-'+m.group('d')+' '+m.group('H')+'-'+m.group('M')+'-'+m.group('S')
            return datetime.datetime.strptime(time_str, '%Y-%m-%d %H-%M-%S')
        return None
        
    def moveFile(self, file:str):
        print(file)
        if os.path.isdir(self.__raw_dir) is False:
            os.mkdir(self.__raw_dir)
        shutil.move(self.__data_dir + '/' + file,
        self.__raw_dir+ '/' + file)

    def removeFile(self, file:str):
        os.remove(self.__raw_dir + '/' + file)

    def backup(self, spanDays:int):
        current = jst.now().replace(microsecond=0)
        tdelta = datetime.timedelta(days=spanDays)
        files = os.listdir(self.__data_dir)
        files_file = [f for f in files if os.path.isfile(os.path.join(self.__data_dir, f)) and '.csv' in f]
        for item in files_file:
            if self.getFileDate(item) is None:
                continue
            if current > self.getFileDate(item) + tdelta:
                self.moveFile(item)

    def delete(self, spanDays:int):
        current = jst.now().replace(microsecond=0)
        tdelta = datetime.timedelta(days=spanDays)
        if os.path.isdir(self.__raw_dir) is True:
            files = os.listdir(self.__raw_dir)
            files_file = [f for f in files if os.path.isfile(os.path.join(self.__raw_dir, f)) and '.csv' in f]
            for item in files_file:
                if self.getFileDate(item) is None:
                    self.removeFile(item)
                if current > self.getFileDate(item) + tdelta:
                    self.removeFile(item)
