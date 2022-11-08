from get_chrome_driver import GetChromeDriver
from selenium import webdriver
import socket
import time
import pandas as pd
import expansion
from scripts import seleniumDriverWrapper as wrap
from scripts import cardrush
from scripts import hareruya2
from scripts import magi
from scripts import torecolo
from scripts import marcketConfig

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

for exp in expansion.getList():
    dfExp = pd.read_csv('./data/card/'+exp+'.csv', header=0, encoding='utf_8_sig')
    if time.time() - start > 480:
        break
    for index, row in dfExp.iterrows():
        if time.time() - start > 480:
            break
        if pd.isnull(row['master_id']):
            print('skip:'+row['name'])
            continue
        if row['is_mirror'] == 'TRUE':
            print('skip:'+row['name'])
            continue

        dataDir = './data/marcket/'+row['master_id']
        conf = marcketConfig.marcketConfigIO(dataDir)
        conf.load()

        if conf.checkUpdate('torecolo', 6):
            torecoloBot.download(wrapper, row['name'], row['cn'], dataDir)
            conf.update('torecolo')
            conf.save()
        if conf.checkUpdate('cardrush', 6):
            cardrushBot.download(wrapper, row['name'], row['cn'], dataDir)
            conf.update('cardrush')
            conf.save()
        if conf.checkUpdate('hareruya2', 6):
            hareruya2Bot.download(wrapper, row['name'], row['cn'], dataDir)
            conf.update('hareruya2')
            conf.save()
        if conf.checkUpdate('magi', 6):
            magiBot.download(wrapper, 1, row['name'], row['expansion'], row['cn'], row['rarity'], dataDir)
            conf.update('magi')
            conf.save()

wrapper.end()
