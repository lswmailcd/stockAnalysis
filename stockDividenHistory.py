#coding:utf-8
import os
from sqlalchemy import create_engine
import numpy as np
import tushare as ts
import stockTools as sT
import Graph
import matplotlib.pyplot as plt
import time

code = "600578"
YEARSTART = 2008  #统计起始时间
YEAREND = 2019
reportYearLast = 2017
yearNow = 2019
moneyInvest = 10000.0

name, yearToMarket, _, _ = sT.getStockBasics(code)
if yearToMarket == 0:
    print code, name, u"上市时间不详!"
    exit(1)
if yearToMarket>=YEARSTART: YEARSTART = yearToMarket+1
str = raw_input("不检查历史数据继续请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    y = YEAREND + 1
    print "checking asset_debt..."
    if sT.checkStockAssetDebt(code, YEARSTART, reportYearLast) == False: exit(1)
    print "checking reports..."
    found, YEARSTART = sT.checkStockReport(code, YEARSTART, reportYearLast)
    if found==False : exit(1)
    print "checking distrib..."
    if sT.checkDistrib(code, YEARSTART, reportYearLast) == False: exit(1)
    print "checking DONE!"

YEARList = [0]*(YEAREND-YEARSTART+1)
DividenRateList = [0]*(YEAREND-YEARSTART+1)
conn = sT.createDBConnection()
i = 0
for year in range(YEARSTART, YEAREND +1):
    YEARList[i] = year
    if year!= yearNow:
        found, price, m, d = sT.getClosePriceForward(code, sT.getDateString(year,12,31))
    else:
        found, price, m, d = sT.getClosePriceForward(code, time.strftime('%Y-%m-%d', time.localtime(time.time())))
    if found:
        nStock = moneyInvest / price
        print code, name, year, "年，nStock=", nStock, "Price=", price
    else:
        print code, name, year,"年，价格获取失败！"
    try:
        sqlString = "select distrib from stockreport_"
        sqlString += "%s" % (year)
        sqlString += "_4 where code="
        sqlString += code
        ret = conn.execute(sqlString)
    except Exception, e:
        print "ERROR: ", code, name, "connect database failure!"
        print e
    if year <= reportYearLast:
        resultDistrib = ret.first()
        if resultDistrib is None or resultDistrib.distrib is None:
            print "WARNING:", code, name, year, u"年分红数据不详，数据库年报分红数据获取失败！此年可能无分红！"
            DividenRateList[i] = 0.0
            r = 0.0
            rLast = 0.0
        else:
            r, s = sT.getDistrib(resultDistrib.distrib)
            rLast = r
    else:
        r = rLast
    DividenRateList[i] = r*nStock/moneyInvest
    print code, name, "distrib=",r,"股息率: %.2f%%" %(DividenRateList[i]*100.0)
    i=i+1

fig = plt.figure()
ax = fig.add_subplot(1,1,1)
Graph.drawColumnChat( ax, YEARList, DividenRateList, YEARList, DividenRateList, \
                      name.decode('utf8'), u'', u'历年分红率', 20, 0.5, bPercent=True)
plt.show()
