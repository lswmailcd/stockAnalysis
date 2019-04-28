#encoding:utf-8

from sqlalchemy import create_engine
import numpy as np
import Graph
import tushare as ts
import time
import matplotlib.pyplot as plt
import stockTools as sT

code = "000513"
YEARSTART = 2008#统计起始时间
DATA2WATCH =[]#["2014-01-24","2015-05-25","2018-01-12","2018-06-08"] #指定观察时间点
#千禾味业["2017-05-31","2017-10-12","2018-02-23","2018-06-05","2018-09-17","2019-04-01"] #指定观察时间点


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
PEDiscList = []
PriceList = []
EPSTTMList=[]
EPSTTMdiscountList=[]
EPS=0.0
totalStock = 0.0
closePrice=0.0
netProfits=0.0
foundData = False
strInfo = ""
for year in range(YEARSTART, y+1):
    #DATA2WATCH.append(sT.getDateString(year, 4, 30))
    #DATA2WATCH.append(sT.getDateString(year, 7, 31))
    #DATA2WATCH.append(sT.getDateString(year, 10, 31))
    YEARList.append(year)
    foundData, EPS = sT.getStockEPS(code, year, 4)
    _, epsdic = sT.getStockEPSdiscount(code, year, 4)
    totalStock = sT.getStockCount(code, year, 4)  # 得到总市值
    if not foundData:
        strInfo = "%s" %(code) + name + "%s" %(year) + "年4季度,数据库中无此股票EPS!epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps"
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData_Q3, EPS_Q3 = sT.getStockEPS(code, year, 3)
        _, epsdic_Q3 = sT.getStockEPSdiscount(code, year, 3)
        foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year-1, 4)
        _, epsdic_LQ4 = sT.getStockEPSdiscount(code, year-1, 4)
        foundData_LQ3, EPS_LQ3 = sT.getStockEPS(code, year-1, 3)
        _, epsdic_LQ3 = sT.getStockEPSdiscount(code, year-1, 3)
        EPS = EPS_Q3 + EPS_LQ4 - EPS_LQ3
        epsdic = epsdic_Q3 + epsdic_LQ4 - epsdic_LQ3
        totalStock = sT.getStockCount(code, year, 3)  # 得到总市值
        if not foundData_Q3:
            strInfo = "%s" % (code) + name + "%s" % (year) + "年3季度,数据库中无此股票EPS!epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps"
            # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
            foundData_Q2, EPS_Q2 = sT.getStockEPS(code, year, 2)
            _, epsdic_Q2 = sT.getStockEPSdiscount(code, year, 2)
            foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year - 1, 4)
            _, epsdic_LQ4 = sT.getStockEPSdiscount(code, year-1, 4)
            foundData_LQ2, EPS_LQ2 = sT.getStockEPS(code, year - 1, 2)
            _, epsdic_LQ2 = sT.getStockEPSdiscount(code, year-1, 2)
            EPS = EPS_Q2 + EPS_LQ4 - EPS_LQ2
            epsdic = epsdic_Q2 + epsdic_LQ4 - epsdic_LQ2
            totalStock = sT.getStockCount(code, year, 2)  # 得到总市值
            if not foundData_Q2:
                strInfo = "%s" % (code) + name + "%s" % (year) + "年2季度,数据库中无此股票EPS!epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps"
                # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
                foundData_Q1, EPS_Q1 = sT.getStockEPS(code, year, 1)
                _, epsdic_Q1 = sT.getStockEPSdiscount(code, year, 1)
                foundData_LQ4, EPS_LQ4 = sT.getStockEPS(code, year - 1, 4)
                _, epsdic_LQ4 = sT.getStockEPSdiscount(code, year - 1, 4)
                foundData_LQ1, EPS_LQ1 = sT.getStockEPS(code, year - 1, 1)
                _, epsdic_LQ1 = sT.getStockEPSdiscount(code, year - 1, 1)
                EPS = EPS_Q1 + EPS_LQ4 - EPS_LQ1
                epsdic = epsdic_Q1 + epsdic_LQ4 - epsdic_LQ1
                totalStock = sT.getStockCount(code, year, 1)  # 得到总市值
                if not foundData_Q1:
                    strInfo = "%s" % (code) + name + "%s" % (year) + "年1季度,数据库中无此股票EPS!eps = 去年4季报（去年年报）"
                    # eps = 去年4季报（去年年报）
                    foundData, EPS = sT.getStockEPS(code, year-1, 4)
                    _, epsdic = sT.getStockEPSdiscount(code, year - 1, 4)
                    totalStock = sT.getStockCount(code, year-1, 4)  # 得到总市值
                    if not foundData:
                        strInfo = "%s," % (code) + name + "%s," % (year-1) + "年4季度, 数据库中无此股票EPS!采用去年3季报eps+前年4季报eps-前年3季报eps"
                        # epsTTM = 去年3季报eps+前年4季报eps-前年3季报eps
                        foundData_LQ3, EPS_LQ3 = sT.getStockEPS(code, year-1, 3)
                        _, epsdic_LQ3 = sT.getStockEPSdiscount(code, year - 1, 3)
                        foundData_LLQ4, EPS_LLQ4 = sT.getStockEPS(code, year - 2, 4)
                        _, epsdic_LLQ4 = sT.getStockEPSdiscount(code, year - 2, 4)
                        foundData_LLQ3, EPS_LLQ3 = sT.getStockEPS(code, year - 2, 3)
                        _, epsdic_LLQ3 = sT.getStockEPSdiscount(code, year - 2, 3)
                        EPS = EPS_LQ3 + EPS_LLQ4 - EPS_LLQ3
                        epsdic = epsdic_LQ3 + epsdic_LLQ4 - epsdic_LLQ3
                        totalStock = sT.getStockCount(code, year-1, 3)  # 得到总市值
    EPSTTMList.append(EPS)
    EPSTTMdiscountList.append(epsdic)
    print strInfo
    if year>LASTYEAR:
        _, closePrice, _, _ = sT.getClosePriceForward(code, date )
    else:
        _, closePrice, m2, d2 = sT.getClosePriceForward(code, year, 12, 31)
    PEList.append(closePrice / EPS)
    PEDiscList.append(closePrice / epsdic)
    PriceList.append(closePrice * totalStock)  # 得到当年总市值
    print sT.getDateString(year,m2,d2),",BasicPETTM=",PEList[-1],", ","discountPETTM=",PEList[-1],\
                           ",priceTotal=", round(PriceList[-1]/10**4,0), ",EPSTTM=",EPS, ",EPSDicountTTM=",epsdic

    for dt in DATA2WATCH:
        y1,m1,d1=sT.splitDateString(dt)
        if y1==year:
            qt = sT.getQuarter(m1)
            if qt==1:
                foundData, EPSTTM = sT.getStockEPSTTM(code, y1-1, 4)
                _, EPSdiscountTTM = sT.getStockEPSdiscountTTM(code, y1 - 1, 4)
            else:
                foundData, EPSTTM = sT.getStockEPSTTM(code, y1, qt-1)
                _, EPSdiscountTTM = sT.getStockEPSdiscountTTM(code, y1 - 1, 4)
            if foundData:
                foundData, closePrice, m1T, d1T = sT.getClosePriceForward(code, dt)
                qt = sT.getQuarter(m1T)
                if qt == 1:
                    totalStock = sT.getStockCount(code, y1 - 1, 4)
                else:
                    totalStock = sT.getStockCount(code, y1, qt - 1)
            if foundData:
                YEARList.append(y1)
                PriceList.append(closePrice * totalStock)
                PEList.append(closePrice / EPSTTM)
                PEDiscList.append(closePrice / EPSdiscountTTM)
                print dt, ",BasicPETTM=",PEList[-1],", ","discountPETTM=",PEList[-1],\
                      ",priceTotal=", round(PriceList[-1]/10**4,0), ",EPSTTM=",EPS, ",EPSDicountTTM=",epsdic
                EPSTTMList.append(EPSTTM)
                EPSTTMdiscountList.append(EPSdiscountTTM)

for i in range(len(PriceList)):
    PriceList[i] = PriceList[i]/10**4

min = min(PEList)
max = max(PEList)
a = [x for x in PEList if x > min]
a = [x for x in a if x < max]
quantile = np.percentile(a, (20, 50, 80), interpolation='midpoint')
print "PETTM_20%_50%_80%=", quantile

PETTM_MEDIAN = quantile[1]
PETTM_MEDIAN2NOW = (PEList[-1]-PETTM_MEDIAN)/PEList[-1]

fig = plt.figure()
ax1 = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2)
ax3 = fig.add_subplot(3,1,3)
fs = 18
#fig1
Graph.drawColumnChat( ax1, YEARList, PriceList, YEARList, PriceList, name.decode('utf8'), u'', u'总市值(亿元)', fs, 0.5,True)
#fig2
spct = str(round(PETTM_MEDIAN2NOW*100.0,2))
spct = spct + u'$\%$'
Graph.drawColumnChat( ax2, YEARList, PEList,YEARList, PEList, u'', u'', u'BasicPE_TTM('+spct+u")", fs, 0.5)
ax2.axhline(color='green',y=quantile[2])
ax2.axhline(color='red',y=quantile[0])
ax2.axhline(color='orange',y=quantile[1])
xlim = ax2.get_xlim()
fs1 = fs*0.8
ax2.text(xlim[1]+0.01,quantile[2],'80%:'+str(round(quantile[2],2)),fontsize=fs1,color='green')
ax2.text(xlim[1]+0.01,quantile[1],"50%:"+str(round(quantile[1],2)),fontsize=fs1,color='orange')
ax2.text(xlim[1]+0.01,quantile[0],"20%:"+str(round(quantile[0],2)),fontsize=fs1,color='red')
#fig3
Graph.drawColumnChat( ax3, YEARList, PEDiscList,YEARList, PEDiscList, u'', u'', u'DiscEPS_TTM', fs, 0.5)

print code,name,u"历史图绘制完成"
plt.show()