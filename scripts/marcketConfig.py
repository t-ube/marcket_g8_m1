import os
import json
import datetime
from pathlib import Path
from . import jst

# 設定読み書き
class marcketConfigIO():
    def __init__(self, _out_dir):
        self.__out_dir = _out_dir
        self.__file = self.__out_dir + '/config.json'
        self.data = {
                "marcket": {
                    "torecolo": {
                        "updated_at": None
                    },
                    "toretoku": {
                        "updated_at": None
                    },
                    "cardrush": {
                        "updated_at": None
                    },
                    "magi": {
                        "updated_at": None
                    },
                    "mercari": {
                        "updated_at": None
                    },
                    "hareruya2": {
                        "updated_at": None
                    }
                }
            }

    def load(self):
        if os.path.isfile(self.__file) == False:
            return
        with open(self.__file, encoding='utf_8_sig') as f:
            self.data = json.load(f)

    def enableMarcket(self, marcket):
        if 'marcket' not in self.data:
            return
        if marcket not in self.data['marcket']:
            if marcket == 'marcari':
                self.data['marcket'][marcket] = {
                    "updated_at": None
                }

    def checkUpdate(self, marcket, spanHours):
        current = jst.now().replace(microsecond=0)
        if 'marcket' not in self.data:
            return False
        if marcket not in self.data['marcket']:
            if marcket == 'hareruya2':
                self.data['marcket'][marcket] = {
                    "updated_at": None
                }
            else:
                return False
        if self.data['marcket'][marcket]['updated_at'] is None:
            return True
        tdelta = datetime.timedelta(hours=spanHours)
        tdatetime = datetime.datetime.strptime(self.data['marcket'][marcket]['updated_at'], '%Y-%m-%d %H:%M:%S')
        if current > tdatetime + tdelta:
            return True
        return False

    def update(self, marcket):
        dt = jst.now().replace(microsecond=0)
        self.data['marcket'][marcket]['updated_at'] = str(dt)

    def save(self):
        Path(self.__out_dir).mkdir(parents=True, exist_ok=True)
        with open(self.__file, 'w') as f:
            json.dump(self.data, f, indent=4)
