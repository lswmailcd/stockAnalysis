#encoding:utf-8

from sqlalchemy import create_engine
import numpy as np
import Graph
import tushare as ts
import time
import matplotlib.pyplot as plt
import stockTools as sT

code = "600519"
YEARSTART = 2008 #统计起始时间
DATA2WATCH =[]#["2014-01-24","2015-05-25","2018-01-12","2018-06-08"] #指定观察时间点

date = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
y, m, d = sT.splitDateString(date)
LASTYEAR = y-1
name, yearToMarket, _, _ = sT.getStockBasics(code)
if yearToMarket == 0:
    print code, name, u"上市时间不详!"
    exit(1)
if yearToMarket>=YEARSTART: YEARSTART = yearToMarket+1
strInfo = raw_input("不检查历史数据继续请按'回车',如需检查请按'c',退出请按'q': ")
if strInfo=="q" : exit(0)
if strInfo=="c" :
    print "checking asset_debt..."
    if sT.checkStockAssetDebt(code, YEARSTART, y) == False: exit(1)
    print "checking reports..."
    found, YEARSTART = sT.checkStockReport(code, YEARSTART, y)
    if found==False : exit(1)
    print "checking distrib..."
    if sT.checkDistrib(code, YEARSTART, LASTYEAR) == False: exit(1)
    print "checking DONE!"

YEARList = []
PEList = []
PriceList = []
EPS=0.0
totalStock = 0.0
closePrice=0.0
netProfits=0.0
foundData = False
strInfo = ""
for year in range(YEARSTART, y+1):
    YEARList.append(year)
    foundData, EPS = sT.getStockEPS(code, year, 4)
    totalStock = sT.getStockCount(code, year, 4)  # 得到总市值
    if not foundData:
        strInfo = "%s" %(code) + name + "%s" %(year) + "年4季度,数据库中无此股票EPS!epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps"
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData_Q3, EPS_Q3 = sT.getStockEPS(code, year, 3)
        foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year-1, 4)
        foundData_LQ3, EPS_LQ3 = sT.getStockEPS(code, year-1, 3)
        EPS = EPS_Q3 + EPS_LQ4 - EPS_LQ3
        totalStock = sT.getStockCount(code, year, 3)  # 得到总市值
        if not foundData_Q3:
            strInfo = "%s" % (code) + name + "%s" % (year) + "年3季度,数据库中无此股票EPS!epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps"
            # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
            foundData_Q2, EPS_Q2 = sT.getStockEPS(code, year, 2)
            foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year - 1, 4)
            foundData_LQ2, EPS_LQ2 = sT.getStockEPS(code, year - 1, 2)
            EPS = EPS_Q2 + EPS_LQ4 - EPS_LQ2
            totalStock = sT.getStockCount(code, year, 2)  # 得到总市值
            if not foundData_Q2:
                strInfo = "%s" % (code) + name + "%s" % (year) + "年2季度,数据库中无此股票EPS!epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps"
                # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
                foundData_Q1, EPS_Q1 = sT.getStockEPS(code, year, 1)
                foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year - 1, 4)
                foundData_LQ1, EPS_LQ1 = sT.getStockEPS(code, year - 1, 1)
                EPS = EPS_Q1 + EPS_LQ4 - EPS_LQ1
                totalStock = sT.getStockCount(code, year, 1)  # 得到总市值
                if not foundData_Q1:
                    strInfo = "%s" % (code) + name + "%s" % (year) + "年1季度,数据库中无此股票EPS!eps = 去年4季报（去年年报）"
                    # eps = 去年4季报（去年年报）
                    foundData, EPS = sT.getStockEPS(code, year-1, 4)
                    totalStock = sT.getStockCount(code, year-1, 4)  # 得到总市值
                    if not foundData:
                        strInfo = "%s," % (code) + name + "%s," % (year-1) + "年4季度, 数据库中无此股票EPS!采用去年3季报eps+前年4季报eps-前年3季报eps"
                        # epsTTM = 去年3季报eps+前年4季报eps-前年3季报eps
                        foundData_LQ3, EPS_LQ3 = sT.getStockEPS(code, year-1, 3)
                        foundData_LLQ4, EPS_LLQ4 = sT.getStockEPS(code, year - 2, 4)
                        foundData_LLQ3, EPS_LLQ3 = sT.getStockEPS(code, year - 2, 3)
                        EPS = EPS_LQ3 + EPS_LLQ4 - EPS_LLQ3
                        totalStock = sT.getStockCount(code, year-1, 3)  # 得到总市值
    print strInfo
    if year>LASTYEAR:
        _, closePrice, _, _ = sT.getClosePriceForward(code, date )
    else:
        _, closePrice, _, _ = sT.getClosePriceForward(code, year, 12, 31)
    PEList.append(closePrice / EPS)
    PriceList.append(closePrice * totalStock)  # 得到当年总市值
    print year,"年，EPSTTM=",EPS

    for dt in DATA2WATCH:
        y1,m1,d1=sT.splitDateString(dt)
        if y1==year:
            foundData, EPSTTM = sT.getStockEPSTTM(code, y1, sT.getQuarter(m1))
            if foundData:
                foundData, closePrice, m1T, d1T = sT.getClosePriceForward(code, dt)
                totalStock = sT.getStockCount(code, y1, sT.getQuarter(m1))
            if foundData:
                YEARList.append(y1)
                PriceList.append(closePrice * totalStock)
                PEList.append(closePrice / EPSTTM)
                print dt, "PETTM=", closePrice / EPSTTM,"priceTotal=",round(closePrice * totalStock/10**4,0)

for i in range(len(PriceList)):
    PriceList[i] = PriceList[i]/10**4


quantile = np.percentile(PEList, (20, 50, 80), interpolation='midpoint')
print quantile

PETTM_MEDIAN = np.median(PEList)
PETTM_MEDIAN2NOW = (PEList[-1]-PETTM_MEDIAN)/PEList[-1]
print "PETTM_MEDIAN=",PETTM_MEDIAN

fig = plt.figure()
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
#fig1
Graph.drawColumnChat( ax1, YEARList, PriceList, YEARList, PriceList, name.decode('utf8'), u'', u'总市值(亿元)', 20, 0.5,True)
#fig2
spct = str(round(PETTM_MEDIAN2NOW*100.0,2))
spct = spct + u'$\%$'
Graph.drawColumnChat( ax2, YEARList, PEList,YEARList, PEList, u'', u'', u'PE_TTM('+spct+u")", 20, 0.5)
ax2.axhline(color='green',y=quantile[2])
ax2.axhline(color='red',y=quantile[0])
ax2.axhline(color='orange',y=quantile[1])
ax2.text(y+1,quantile[2],'80%',fontsize=20,color='green')
ax2.text(y+1,quantile[1],"50%",fontsize=20,color='orange')
ax2.text(y+1,quantile[0],"20%",fontsize=20,color='red')

print code,name,u"历史图绘制完成"
plt.show()