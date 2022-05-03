#encoding:utf-8

import os
from sqlalchemy import create_engine
import stockGlobalSpace as sG
import numpy as np
import Graph
import tushare as ts
import time
import matplotlib.pyplot as plt
import stockTools as sT
import stockDataChecker as ck

code = "300003"
REPORTYEARLAST = 2021 #最新年报时间

YEARSTART = REPORTYEARLAST-10
DATA2WATCH =[]#指定观察时间点
#贵州茅台["2018-06-12","2015-05-25","2012-07-13"]
#五粮液["2018-01-15","2015-06-08","2007-10-15"]
#涪陵榨菜["2018-07-31","2015-06-08","2013-10-08"]
#恒瑞医药["2020-07-15","2018-05-28","2015-05-27"]
#通化东宝["2018-07-13","2015-05-26"]
#丽珠集团["2018-01-24","2020-08-05","2015-05-26"]
#伊利股份["2018-01-23","2019-07-02","2015-05-26","2013-10-21"]
#千禾味业["2017-05-31","2017-10-12","2018-02-23","2018-06-05","2018-09-17","2019-04-01"] #指定观察时间点

date = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
#DATA2WATCH.append(date)
y, m, d = sT.splitDateString(date)
LASTYEAR = y-1
name, yearToMarket, _, _ = sT.getStockBasics(code)
if yearToMarket == 0:
    print( code, name, u"上市时间不详!")
    exit(1)
print( "{}:{},上市年份{}年".format(code, name, yearToMarket))
if yearToMarket>=YEARSTART: YEARSTART = yearToMarket+1
sG.lock.acquire()
strInfo = input("不检查历史数据继续请按'回车',如需检查请按'c',退出请按'q': ")
sG.lock.release()
if strInfo=="q" : exit(0)
ck.subprocess(code, YEARSTART-1, y, True) if strInfo=="c" else ck.subprocess(code, YEARSTART-1, y)


YEARList = []
PEList = []
PEDiscList = []
PriceList = []
ETTMList=[]
ETTMdiscountList=[]
earnList = []
roeList = []
EPS=0.0
totalStock = 0.0
closePrice=0.0
netProfits=0.0
foundData = False
strInfo = ""
for year in range(YEARSTART, y+1):
    YEARList.append(year)
    foundData, EPS = sT.getStockEPSTTM(code, year, 4)
    if foundData:
        totalStock = sT.getStockShare(code, year, 12, 31)  # 得到总市值
        ETTMList.append((year, 12, EPS*totalStock))
        _, epsdic = sT.getStockEPSdiscountTTM(code, year, 4)
        ETTMdiscountList.append((year, 12, epsdic*totalStock))
        found, earnRate = sT.getStockEarnIncRate(code, year, 4)
        earnList.append((year, 12, earnRate)) if found else earnList.append((year, 12, 0.0))
        _, roe = sT.getStockROE(code, year, 4)
        roeList.append((year, 12, roe))
    else:
        roeList.append((year, 12, 0.0))
        strInfo = "%s" %(code) + name + "%s" %(year) + "年4季度,数据库中无此股票EPS!epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps"
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData, EPS = sT.getStockEPSTTM( code, year, 3 )
        if foundData:
            totalStock = sT.getStockShare(code, year, 12, 31)  # 得到总市值
            ETTMList.append((year, 12, EPS*totalStock))
            _, earnRate = sT.getStockEarnIncRate(code, year, 3)
            earnList.append((year, 12, earnRate))
            _, disEPS = sT.getStockEPSdiscountTTM(code, year, 3)
            ETTMdiscountList.append((year, 12, disEPS*totalStock))
        else:
            strInfo = "%s" % (code) + name + "%s" % (year) + "年3季度,数据库中无此股票EPS!epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps"
            # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
            foundData, EPS = sT.getStockEPSTTM(code, year, 2)
            if foundData:
                totalStock = sT.getStockShare(code, year, 9, 30)  # 得到总市值
                ETTMList.append((year, 9, EPS*totalStock))
                _, disEPS = sT.getStockEPSdiscountTTM(code, year, 2)
                ETTMdiscountList.append((year, 9, disEPS*totalStock))
                _, earnRate = sT.getStockEarnIncRate(code, year, 2)
                earnList.append((year, 9, earnRate))
            else:
                strInfo = "%s" % (code) + name + "%s" % (year) + "年2季度,数据库中无此股票EPS!epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps"
                # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
                foundData, EPS = sT.getStockEPSTTM(code, year, 1)
                if foundData:
                    totalStock = sT.getStockShare(code, year, 6, 30)  # 得到总市值
                    ETTMList.append((year, 6, EPS*totalStock))
                    _, disEPS = sT.getStockEPSdiscountTTM(code, year, 1)
                    ETTMdiscountList.append((year, 6, disEPS*totalStock))
                    _, earnRate = sT.getStockEarnIncRate(code, year, 1)
                    earnList.append((year, 6, earnRate))
                else:
                    strInfo = "%s" % (code) + name + "%s" % (year) + "年1季度,数据库中无此股票EPS!eps = 去年4季报（去年年报）"
                    # eps = 去年4季报（去年年报）
                    foundData, EPS = sT.getStockEPSTTM(code, year-1, 4)
                    earnList.append((year, 3, 0.0))
                    if foundData:
                        totalStock = sT.getStockShare(code, year, 3, 31)  # 得到总市值
                        ETTMList.append((year, 3, EPS*totalStock))
                        ETTMdiscountList.append((year, 3, 0.0))
                    else:
                        strInfo = "%s," % (code) + name + "%s" % (year-1) + "年4季度, 数据库中无此股票EPS!采用去年3季报eps+前年4季报eps-前年3季报eps"
                        # epsTTM = 去年3季报eps+前年4季报eps-前年3季报eps
                        foundData, EPS = sT.getStockEPSTTM(code, year - 1, 3)
                        totalStock = sT.getStockShare(code, year-1, 12, 31)  # 得到总市值
                        ETTMList.append((year - 1, 12, EPS*totalStock))
                        _, epsdic = sT.getStockEPSdiscountTTM(code, year - 1, 3)
                        ETTMdiscountList.append((year-1, 12, epsdic*totalStock))

    # EPSTTMList.append(EPS)
    # EPSTTMdiscountList.append(epsdic)
    print(strInfo)
    if year>LASTYEAR:
        _, closePrice, dRet = sT.getClosePriceForward(code, date )
    else:
        _, closePrice, dRet = sT.getClosePriceForward(code, year, 12, 31)
    y2, m2, d2 = sT.splitDateString(dRet)
    PEList.append(0 if EPS<=0 else closePrice / EPS)
    PEDiscList.append(0 if epsdic<=0 else closePrice / epsdic)
    PriceList.append(closePrice * totalStock)  # 得到当年总市值
    print( sT.getDateString(year,m2,d2),",BasicPETTM=",PEList[-1],", ","discountPETTM=",PEDiscList[-1],\
                           "stockshare=",totalStock,"priceTotal=", round(PriceList[-1]/10**8,2) )
    drawPE = PEList[-1]
    for dt in DATA2WATCH:
        y1,m1,d1=sT.splitDateString(dt)
        earnList.append((y1, m1, 0.0))
        roeList.append((year, m1, 0))
        if y1==year:
            foundData = False
            qt = sT.createCalender().getQuarter(m1)
            if qt==1:
                foundData, EPSTTM = sT.getStockEPSTTM(code, y1-1, 4)
                _, EPSdiscountTTM = sT.getStockEPSdiscountTTM(code, y1 - 1, 4)
                totalStock = sT.getStockShare(code, y1, m1, d1)  # 得到总市值
            else:
                qt = qt - 1#本季度报表没有出来，因此使用上季度报表
                while qt>0 and not foundData:
                    foundData, EPSTTM = sT.getStockEPSTTM(code, y1, qt)
                    if not foundData: qt = qt - 1;continue;
                    totalStock = sT.getStockShare(code, y1, m1, d1)  # 得到总市值
                    _, EPSdiscountTTM = sT.getStockEPSdiscountTTM(code, y1, qt)
            if foundData:
                foundData, closePrice, m1T, d1T = sT.getClosePriceForward(code, dt)
                YEARList.append(y1)
                #factor:处理送股造成的股价变化
                factor = sT.getStockShare(code, y1, m1T, d1T)/totalStock
                if factor>1.0:
                    PriceList.append(closePrice * totalStock * factor)
                    PEList.append(closePrice*factor / EPSTTM)
                    PEDiscList.append(closePrice*factor / EPSdiscountTTM)
                else:
                    PriceList.append(closePrice * totalStock)
                    PEList.append(closePrice / EPSTTM)
                    PEDiscList.append(closePrice / EPSdiscountTTM)
                ETTMList.append((y1, m1, EPSTTM*totalStock))
                ETTMdiscountList.append((y1, m1, EPSdiscountTTM*totalStock))
                print( dt, ",BasicPETTM=",PEList[-1],", ","discountPETTM=",PEDiscList[-1],"stockshare=",totalStock,\
                      ",priceTotal=", round(PriceList[-1]/10**8,2) )

for i in range(len(PriceList)):
    PriceList[i] = PriceList[i]/10**8

ETTMList.sort(key=lambda x:(x[0],x[1]))
ETTMdiscountList.sort(key=lambda x:(x[0],x[1]))
earnList.sort(key=lambda x:(x[0],x[1]))
roeList.sort(key=lambda x:(x[0],x[1]))

ETTMList = [x[2] for x in ETTMList]
ETTMdiscountList = [x[2] for x in ETTMdiscountList]
earnList = [x[2]/100.0 for x in earnList]
roeList = [x[2]/100.0 for x in roeList]
EPSTTMRateList, EPSTTMdiscountRateList = [0.0],[0.0]
for i in range(1, len(YEARList)):
    EPSTTMRateList.append( (ETTMList[i]-ETTMList[i-1])/ETTMList[i-1] )
    EPSTTMdiscountRateList.append((ETTMdiscountList[i] - ETTMdiscountList[i - 1]) / ETTMdiscountList[i - 1])

min = min(PEList)
max = max(PEList)
a = [x for x in PEList if x > min]
a = [x for x in a if x < max]
quantile = np.percentile(a, (20, 50, 80), interpolation='midpoint')
print("PETTM_20%_50%_80%=", quantile)

PETTM_MEDIAN = quantile[1]
PETTM_MEDIAN2NOW = (PEList[-1]-PETTM_MEDIAN)/PEList[-1]

fig = plt.figure()
figNum = 7
ax = []
for i in range(1,figNum+1):
    ax.append(fig.add_subplot(figNum,1,i))
fs = 10
j=0
#fig1
Graph.drawColumnChat( ax[j], YEARList, PriceList, YEARList, PriceList, name, u'', u'总市值(亿元)', fs, 0.5)
ax[j].axhline(color='cornflowerblue',y=PriceList[-1])
j+=1
#fig2
spct = str(round(PETTM_MEDIAN2NOW*100.0,2))
spct = spct + u'$\%$'
Graph.drawColumnChat( ax[j], YEARList, PEList,YEARList, PEList, u'', u'', u'BasicPE_TTM('+spct+u")", fs, 0.5)
ax[j].axhline(color='green',y=quantile[2])
ax[j].axhline(color='red',y=quantile[0])
ax[j].axhline(color='orange',y=quantile[1])
xlim = ax[j].get_xlim()
fs1 = fs*0.8
ax[j].text(xlim[1]+0.01,quantile[2],'80%:'+str(round(quantile[2],2)),fontsize=fs1,color='green')
ax[j].text(xlim[1]+0.01,quantile[1],"50%:"+str(round(quantile[1],2)),fontsize=fs1,color='orange')
ax[j].text(xlim[1]+0.01,quantile[0],"20%:"+str(round(quantile[0],2)),fontsize=fs1,color='red')
ax[j].axhline(color='cornflowerblue',y=drawPE)
j+=1
#fig3
Graph.drawColumnChat( ax[j], YEARList, PEDiscList,YEARList, PEDiscList, u'', u'', u'DiscPE_TTM', fs, 0.5)
ax[j].axhline(color='cornflowerblue',y=PEDiscList[-1])
j+=1
#fig4
Graph.drawColumnChat( ax[j], YEARList, EPSTTMRateList,YEARList, EPSTTMRateList, u'', u'', u'adjustE_TTM_Rate', fs, 0.5, bPercent=True)
j+=1
#fig4
Graph.drawColumnChat( ax[j], YEARList, EPSTTMdiscountRateList,YEARList, EPSTTMdiscountRateList, u'', u'', u'DiscE_TTM_Rate', fs, 0.5, bPercent=True)
j+=1
#fig5
Graph.drawColumnChat( ax[j], YEARList, earnList,YEARList, earnList, u'', u'', u'earnIncRate', fs, 0.5, bPercent=True)
j+=1
#fig6
Graph.drawColumnChat( ax[j], YEARList, roeList,YEARList, roeList, u'', u'', u'ROE', fs, 0.5, bPercent=True)
j+=1
print( code,name,u"历史图绘制完成")
plt.show()