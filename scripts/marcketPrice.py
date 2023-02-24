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

    def get(self):
        return self.data

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

    def validate(self):
        if self.data['count'] == float('inf'): return False
        if self.data['mean'] == float('inf'): return False
        if self.data['std'] == float('inf'): return False
        if self.data['min'] == float('inf'): return False
        if self.data['25%'] == float('inf'): return False
        if self.data['50%'] == float('inf'): return False
        if self.data['75%'] == float('inf'): return False
        if self.data['max'] == float('inf'): return False
        return True

    def inf2zero(self):
        if self.data['count'] == float('inf'): self.data['count'] = 0.0
        if self.data['mean'] == float('inf'): self.data['mean'] = 0.0
        if self.data['std'] == float('inf'): self.data['std'] = 0.0
        if self.data['min'] == float('inf'): self.data['min'] = 0.0
        if self.data['25%'] == float('inf'): self.data['25%'] = 0.0
        if self.data['50%'] == float('inf'): self.data['50%'] = 0.0
        if self.data['75%'] == float('inf'): self.data['75%'] = 0.0
        if self.data['max'] == float('inf'): self.data['max'] = 0.0

# 価格データの詳細
class priceVolatilityDetails():
    def __init__(self):
        self.data = {
            "basePrice": None,
            "latestPrice": None,
            "percent": None,
        }

    def set(self,base,latest,percent):
        self.data = {
            "basePrice": base,
            "latestPrice": latest,
            "percent": percent,
        }

    def get(self):
        return self.data

    def setDict(self,dict):
        self.data = {
            "basePrice": dict["basePrice"],
            "latestPrice": dict["latestPrice"],
            "percent": dict["percent"],
        }

    def validate(self):
        if self.data['basePrice'] == float('inf'): return False
        if self.data['latestPrice'] == float('inf'): return False
        if self.data['percent'] == float('inf'): return False
        return True

    def inf2zero(self):
        if self.data['basePrice'] == float('inf'): self.data['basePrice'] = 0.0
        if self.data['latestPrice'] == float('inf'): self.data['latestPrice'] = 0.0
        if self.data['percent'] == float('inf'): self.data['percent'] = 0.0


# 価格データ
class priceVolatility():
    def __init__(self):
        self.data = {
            "weekly": None,
            "daily": None,
        }

    def set(self,_data):
        self.data = _data

    def get(self):
        return self.data

    def filterInf(self,data):
        if data == float('inf'):
            return 0.0
        return data

    def validate(self):
        detail = priceVolatilityDetails()
        detail.setDict(self.data["weekly"]["min"])
        if detail.validate() == False: return False
        detail.setDict(self.data["weekly"]["50%"])
        if detail.validate() == False: return False
        detail.setDict(self.data["daily"]["min"])
        if detail.validate() == False: return False
        detail.setDict(self.data["daily"]["50%"])
        if detail.validate() == False: return False
        return True

    def inf2zero(self):
        detail = priceVolatilityDetails()
        detail.setDict(self.data["weekly"]["min"])
        if detail.validate() == False:
            detail.inf2zero()
            self.data["weekly"]["min"] = detail.get()
        detail.setDict(self.data["weekly"]["50%"])
        if detail.validate() == False:
            detail.inf2zero()
            self.data["weekly"]["50%"] = detail.get()
        detail.setDict(self.data["daily"]["min"])
        if detail.validate() == False:
            detail.inf2zero()
            self.data["daily"]["min"] = detail.get()
        detail.setDict(self.data["daily"]["50%"])
        if detail.validate() == False:
            detail.inf2zero()
            self.data["daily"]["50%"] = detail.get()

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
        return {'basePrice': dailyBase, 'latestPrice': dailyCurrent, 'percent': self.filterInf(round(daily*100, 2))}

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
        return {'basePrice': weeklyBase, 'latestPrice': weeklyCurrent, 'percent': self.filterInf(round(weekly*100, 2))}

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

    def getPrice(self):
        return self.data['price']

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

    def getDict(self):
        return self.__df.to_dict(orient='records')

    def addPostgresData(self, df):
        if len(df) > 0:
            df = df.set_index('datetime')
            df.index = pd.to_datetime(df.index, format='%Y-%m-%dT%H:%M:%S')
            df = df.sort_index()
            self.__df = pd.concat([self.__df,df],axis=0)
            self.__df = self.__df.fillna({'count': 0})
            # 新しく重複かつ値がないものを削除
            self.__df = self.__df[~((self.__df.index.duplicated(keep='first')) & (self.__df['count'] == 0))]
            # その後、インデックスが重複した場合には古いデータを破棄する
            self.__df = self.__df[~self.__df.index.duplicated(keep='last')]
            self.__df = self.__df.sort_index()

    def getMigrateData(self):
        df = self.__df.copy()
        df['datetime'] = df.index
        df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d 00:00:00')
        return df.to_dict(orient='records')

# 価格表結合ファイル
class priceLogCsv():
    def __init__(self, data_dir):
        self.__data_dir = data_dir
        self.__calc_dir = self.__data_dir + '/calc'
        self.__file = self.__calc_dir + '/log.csv'

    # 既存の表と結合し、重複を除外する
    def unionExists(self, df):
        if os.path.isfile(self.__file) == False:
            return df
        readDf = pd.read_csv(
            self.__file,
            encoding="utf_8_sig", sep=",",
            header=0)
        df = pd.concat([readDf, df], ignore_index=True,axis=0,sort=False)
        df = df.sort_values(by=['datetime'], ascending=False) 
        df = df[~df.duplicated(subset=['market','date','name','link'],keep='first')]
        return df

    def save(self, df, _date):
        if os.path.isdir(self.__calc_dir) is False:
            os.mkdir(self.__calc_dir)
        tdatetime = datetime.datetime.strptime(_date, '%Y-%m-%d')
        df = self.unionExists(df)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df[df['stock'] > 0]
        df = df[df['datetime'] > tdatetime - datetime.timedelta(days=7)]
        df.to_csv(self.__file,
            header=True,
            index=False,
            encoding='utf_8_sig',
            columns=['market','link','price','name','date','datetime','stock'],
            date_format='%Y-%m-%d %H:%M:%S'
        )

    def convert2JsonLines(self, _json_file):
        if os.path.isfile(self.__file) == False:
            return
        readDf = pd.read_csv(
            self.__file,
            encoding="utf_8_sig", sep=",",
            header=0)
        readDf.to_json(path_or_buf=_json_file,
            force_ascii=False,
            orient='records',
            lines=True)

    def delete2JsonLines(self, _json_file):
        if os.path.isfile(_json_file) == False:
            return
        os.remove(_json_file)

    def convert2Json(self, _json_file):
        if os.path.isfile(self.__file) == False:
            return
        readDf = pd.read_csv(
            self.__file,
            encoding="utf_8_sig", sep=",",
            header=0)
        l = []
        for index, data in readDf.iterrows():
            l.append({
                'market': data['market'],
                'link': data['link'],
                'price': data['price'],
                'name': data['name'],
                'date': data['date'],
                'stock': data['stock'],
            })
        data = {'items': l}
        with open(_json_file, 'w', encoding="utf_8_sig") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def getList(self):
        if os.path.isfile(self.__file) == False:
            return
        readDf = pd.read_csv(
            self.__file,
            encoding="utf_8_sig", sep=",",
            header=0)
        l = []
        for index, data in readDf.iterrows():
            l.append({
                'market': data['market'],
                'link': data['link'],
                'price': data['price'],
                'name': data['name'],
                'date': data['date'],
                'stock': data['stock'],
            })
        return l

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
