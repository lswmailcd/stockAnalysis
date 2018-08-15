# -*- coding: utf-8 -*-

import numpy as np
import xlrd
import tushare as ts
import time
import wave
import pyaudio
import itchat
import pandas as pd
from sqlalchemy import create_engine

bWX = False

idxLimitHigh = 3323
idxLimitLow = 3254
idxAlarm = False
soundRepeatCount = 3

def  sound(s):
    chunk = 1024
    wv = wave.open(s, "rb")
    p = pyaudio.PyAudio()
    # 打开声音输出流
    stream = p.open(format = p.get_format_from_width(wv.getsampwidth()),
                    channels = wv.getnchannels(),
                    rate = wv.getframerate(),
                    output = True)
    # 写声音输出流进行播放
    while True:
        data = wv.readframes(chunk)
        if data == "": break
        stream.write(data)
    stream.close()
    p.terminate()


if bWX:
    itchat.auto_login(hotReload=True)
    account=itchat.get_friends()
    for i in range(18):
        if account[i]['NickName']==u"潇潇":
            UserName = account[i]['UserName']
            break
    UserName = 'filehelper'

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
sqlString = "select * from stockmonitor"
ret = conn.execute(sqlString)
nrow = ret.rowcount
data = ret.fetchall()
stockNum = 0
for i in range(nrow):
    if data[i][2] == "stock":
        stockNum += 1
a = np.zeros([stockNum])
bMonitor = np.zeros([stockNum])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
alarm = np.array(a, dtype=np.bool)
codePriceHighLimit = np.zeros([stockNum])
codePriceLowLimit = np.zeros([stockNum])
idxStock = 0
for i in range(nrow):
    if data[i][2] == "stock":
        code[idxStock] = data[i][0]
        name[idxStock] = unicode(data[i][1], "utf8")
        codePriceHighLimit[idxStock] = data[i][3]
        codePriceLowLimit[idxStock] = data[i][4]
        bMonitor[idxStock] = data[i][5]
        alarm[idxStock] = True
        idxStock += 1
    elif data[i][2] == "sh_index":
        idxLimitHigh = data[i][3]
        idxLimitLow = data[i][4]
        idxAlarm = False
if time.strftime('%H:%M:%S', time.localtime(time.time()))<"09:30:00":
    print "Stock market is not open! Wait for openning......"
while time.strftime('%H:%M:%S', time.localtime(time.time()))<"09:30:00":
    time.sleep(60)
print "Stock monitor start at %s" % (time.strftime('%H:%M:%S', time.localtime(time.time())))
timeStart = time.time()
bReset = False
while True:
    if bReset:
        print "Stock monitor reset at %s" % (time.strftime('%H:%M:%S', time.localtime(time.time())))
        bReset = False
    try:
        while True:
            idxData = ts.get_index()
            idxClose = idxData.values[0,5]
            if idxClose>idxLimitHigh and idxAlarm==False:
                idxAlarm = True
                print u"上证指数高于 %r" % (idxLimitHigh)
                for t in range(soundRepeatCount):
                    sound(r".\resource\tada.wav")
                    time.sleep(1)
            elif idxClose<idxLimitLow and idxAlarm==False:
                idxAlarm = True
                print u"上证指数低于 %r" % (idxLimitLow)
                for t in range(soundRepeatCount):
                    sound(r".\resource\notify.wav")
                    time.sleep(1)
            for i in range(stockNum):
                if bMonitor[i] == 0: continue
                data = ts.get_realtime_quotes(code[i])
                curPrice = float(data.values[0,3])
                if codePriceHighLimit[i]!=0 and alarm[i] and curPrice>codePriceHighLimit[i]:
                    while alarm[i]:
                        m =  code[i]
                        m += " "
                        m += name[i]
                        m += " "
                        m += u"价格>"
                        m += str(codePriceHighLimit[i])
                        if alarm[i]:
                            print m
                            alarm[i] = False
                            for t in range(soundRepeatCount):
                                sound(r".\resource\tada.wav")
                                time.sleep(1)
                            if bWX:
                                r = itchat.send_msg(m, UserName)
                elif codePriceLowLimit[i]!=0 and alarm[i] and curPrice<codePriceLowLimit[i]:
                    while alarm[i]:
                        m =  code[i]
                        m += " "
                        m += name[i]
                        m += " "
                        m += u"价格<"
                        m += str(codePriceLowLimit[i])
                        if alarm[i]:
                            print m
                            alarm[i] = False
                            for t in range(soundRepeatCount):
                                sound(r".\resource\notify.wav")
                                time.sleep(1)
                            if bWX:
                                r = itchat.send_msg(m, UserName)
            time.sleep(20)
    except Exception,e:
        print "error occur at %s" % (time.strftime('%H:%M:%S', time.localtime(time.time())))
        print "time interval after start is %d seconds" % (time.time() - timeStart)
        print e
        bReset = True
        for t in range(soundRepeatCount):
            sound(r".\resource\Windows Balloon.wav")
            time.sleep(1)
