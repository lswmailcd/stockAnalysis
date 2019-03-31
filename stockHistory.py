#encoding:utf-8

from sqlalchemy import create_engine
import numpy as np
import Graph
import tushare as ts
import time
import matplotlib.pyplot as plt
import stockTools as sT

code = "600887"
YEARSTART = 2008  #统计起始时间
LASTYEAR = 2018 #当前时间的上一年

date = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
y, m, d = sT.splitDateString(date)
name, yearToMarket, _, _ = sT.getStockBasics(code)
if yearToMarket == 0:
    print code, name, u"上市时间不详!"
    exit(1)
if yearToMarket>=YEARSTART: YEARSTART = yearToMarket+1
str = raw_input("不检查历史数据继续请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    print "checking asset_debt..."
    if sT.checkStockAssetDebt(code, YEARSTART, y) == False: exit(1)
    print "checking reports..."
    found, YEARSTART = sT.checkStockReport(code, YEARSTART, y)
    if found==False : exit(1)
    print "checking distrib..."
    if sT.checkDistrib(code, YEARSTART, LASTYEAR) == False: exit(1)
    print "checking DONE!"

YEARList = [0]*(y-YEARSTART+1)
PEList = [0]*(y-YEARSTART+1)
PriceList = [0]*(y-YEARSTART+1)
EPS=0.0
totalStock = 0.0
closePrice=0.0
netProfits=0.0
foundData = False
for year in range(YEARSTART, y+1):
    YEARList[year - YEARSTART] = year
    foundData, EPS = sT.getStockEPS(code, year, 4)
    totalStock = sT.getStockCount(code, year, 4)  # 得到总市值
    if not foundData:
        print code, name, year, u"年", 4, u"季度", u"数据库中无此股票!epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps"
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData_Q3, EPS_Q3 = sT.getStockEPS(code, year, 3)
        foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year-1, 4)
        foundData_LQ3, EPS_LQ3 = sT.getStockEPS(code, year-1, 3)
        EPS = EPS_Q3 + EPS_LQ4 - EPS_LQ3
        totalStock = sT.getStockCount(code, year, 3)  # 得到总市值
        if not foundData_Q3:
            print code, name, year, u"年", 3, u"季度", u"数据库中无此股票!epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps"
            # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
            foundData_Q2, EPS_Q2 = sT.getStockEPS(code, year, 2)
            foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year - 1, 4)
            foundData_LQ2, EPS_LQ2 = sT.getStockEPS(code, year - 1, 2)
            EPS = EPS_Q2 + EPS_LQ4 - EPS_LQ2
            totalStock = sT.getStockCount(code, year, 2)  # 得到总市值
            if not foundData_Q2:
                print code, name, year, u"年", 2, u"季度", u"数据库中无此股票!epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps"
                # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
                foundData_Q1, EPS_Q1 = sT.getStockEPS(code, year, 1)
                foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year - 1, 4)
                foundData_LQ1, EPS_LQ1 = sT.getStockEPS(code, year - 1, 1)
                EPS = EPS_Q1 + EPS_LQ4 - EPS_LQ1
                totalStock = sT.getStockCount(code, year, 1)  # 得到总市值
                if not foundData_Q1:
                    print code, name, year, u"年", 1, u"季度", u"数据库中无此股票!eps = 去年4季报（去年年报）"
                    # eps = 去年4季报（去年年报）
                    foundData, EPS = sT.getStockEPS(code, year-1, 4)
                    totalStock = sT.getStockCount(code, year-1, 4)  # 得到总市值
                    if not foundData:
                        print code, name, year-1, u"年", 4, u"季度", u"数据库中无此股票!采用去年3季报eps+前年4季报eps-前年3季报eps"
                        # epsTTM = 去年3季报eps+前年4季报eps-前年3季报eps
                        foundData_LQ3, EPS_LQ3 = sT.getStockEPS(code, year-1, 3)
                        foundData_LLQ4, EPS_LLQ4 = sT.getStockEPS(code, year - 2, 4)
                        foundData_LLQ3, EPS_LLQ3 = sT.getStockEPS(code, year - 2, 3)
                        EPS = EPS_LQ3 + EPS_LLQ4 - EPS_LLQ3
                        totalStock = sT.getStockCount(code, year-1, 3)  # 得到总市值

    if year>LASTYEAR:
        _, closePrice, _, _ = sT.getClosePriceForward(code, date )
    else:
        _, closePrice, _, _ = sT.getClosePriceForward(code, year, 12, 31)
    PEList[year - YEARSTART] = closePrice / EPS
    PriceList[year - YEARSTART] = closePrice * totalStock  # 得到当年总市值

for i in range(y - YEARSTART + 1):
    PriceList[i] = PriceList[i]/10**4

fig = plt.figure()
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
Graph.drawColumnChat( ax1, YEARList, PriceList, YEARList, PriceList, name.decode('utf8'), u'', u'总市值(亿元)', 20, 0.5,True)
Graph.drawColumnChat( ax2, YEARList, PEList,YEARList, PEList, u'', u'', u'PE_TTM', 20, 0.5)
print code,name,u"历史图绘制完成"
plt.show()