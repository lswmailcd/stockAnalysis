#encoding:utf-8


from sqlalchemy import create_engine
import stockGlobalSpace as sG
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
DATA2WATCH.append(date)
y, m, d = sT.splitDateString(date)
LASTYEAR = y-1
name, yearToMarket, _, _ = sT.getStockBasics(code)
if yearToMarket == 0:
    print code, name, u"上市时间不详!"
    exit(1)
if yearToMarket>=YEARSTART: YEARSTART = yearToMarket+1
sG.lock.acquire()
strInfo = raw_input("不检查历史数据继续请按'回车',如需检查请按'c',退出请按'q': ")
sG.lock.release()
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
    YEARList.append(year)
    foundData, EPS = sT.getStockEPS(code, year, 4)
    _, epsdic = sT.getStockEPSdiscount(code, year, 4)
    totalStock = sT.getStockCountQuarter(code, year, 4)  # 得到总市值
    if not foundData:
        strInfo = "%s" %(code) + name + "%s" %(year) + "年4季度,数据库中无此股票EPS!epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps"
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData, EPS = sT.getStockEPSTTM( code, year, 3 )
        epsdic = sT.getStockEPSdiscountTTM( code, year, 3 )
        totalStock = sT.getStockCountQuarter(code, year, 3)  # 得到总市值
        if not foundData:
            strInfo = "%s" % (code) + name + "%s" % (year) + "年3季度,数据库中无此股票EPS!epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps"
            # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
            foundData, EPS = sT.getStockEPSTTM(code, year, 2)
            _, epsdic = sT.getStockEPSdiscountTTM(code, year, 2)
            totalStock = sT.getStockCountQuarter(code, year, 2)  # 得到总市值
            if not foundData:
                strInfo = "%s" % (code) + name + "%s" % (year) + "年2季度,数据库中无此股票EPS!epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps"
                # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
                foundData, EPS = sT.getStockEPSTTM(code, year, 1)
                _, epsdic = sT.getStockEPSdiscountTTM(code, year, 1)
                totalStock = sT.getStockCountQuarter(code, year, 1)  # 得到总市值
                if not foundData:
                    strInfo = "%s" % (code) + name + "%s" % (year) + "年1季度,数据库中无此股票EPS!eps = 去年4季报（去年年报）"
                    # eps = 去年4季报（去年年报）
                    foundData, EPS = sT.getStockEPSTTM(code, year-1, 4)
                    _, epsdic = sT.getStockEPSdiscountTTM(code, year-1, 4)
                    totalStock = sT.getStockCountQuarter(code, year-1, 4)  # 得到总市值
                    if not foundData:
                        strInfo = "%s," % (code) + name + "%s," % (year-1) + "年4季度, 数据库中无此股票EPS!采用去年3季报eps+前年4季报eps-前年3季报eps"
                        # epsTTM = 去年3季报eps+前年4季报eps-前年3季报eps
                        foundData, EPS = sT.getStockEPSTTM(code, year - 1, 3)
                        _, epsdic = sT.getStockEPSdiscountTTM(code, year - 1, 3)
                        totalStock = sT.getStockCountQuarter(code, year-1, 3)  # 得到总市值
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
    print sT.getDateString(year,m2,d2),",BasicPETTM=",PEList[-1],", ","discountPETTM=",PEDiscList[-1],\
                           "stockcount=",totalStock,"priceTotal=", round(PriceList[-1]/10**4,0), ",EPSTTM=",EPS, ",EPSDicountTTM=",epsdic

    for dt in DATA2WATCH:
        y1,m1,d1=sT.splitDateString(dt)
        if y1==year:
            foundData = False
            qt = sT.createCalender().getQuarter(m1)
            if qt==1:
                foundData, EPSTTM = sT.getStockEPSTTM(code, y1-1, 4)
                _, EPSdiscountTTM = sT.getStockEPSdiscountTTM(code, y1 - 1, 4)
                totalStock = sT.getStockCountQuarter(code, y1 - 1, 4)
            else:
                while qt>0 and not foundData:
                    foundData, EPSTTM = sT.getStockEPSTTM(code, y1, qt)
                    if not foundData: qt = qt - 1;continue;
                    _, EPSdiscountTTM = sT.getStockEPSdiscountTTM(code, y1, qt)
                    totalStock = sT.getStockCountQuarter(code, y1, qt)
            if foundData:
                foundData, closePrice, m1T, d1T = sT.getClosePriceForward(code, dt)
                YEARList.append(y1)
                #factor:处理送股造成的股价变化
                factor = sT.getStockCount(code, y1, m1T, d1T)/totalStock
                if factor>1.0:
                    PriceList.append(closePrice * totalStock * factor)
                    PEList.append(closePrice*factor / EPSTTM)
                    PEDiscList.append(closePrice*factor / EPSdiscountTTM)
                else:
                    PriceList.append(closePrice * totalStock)
                    PEList.append(closePrice / EPSTTM)
                    PEDiscList.append(closePrice / EPSdiscountTTM)
                print dt, ",BasicPETTM=",PEList[-1],", ","discountPETTM=",PEDiscList[-1],\
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
Graph.drawColumnChat( ax1, YEARList, PriceList, YEARList, PriceList, name.decode('utf8'), u'', u'总市值(亿元)', fs, 0.5)
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
Graph.drawColumnChat( ax3, YEARList, PEDiscList,YEARList, PEDiscList, u'', u'', u'DiscPE_TTM', fs, 0.5)

print code,name,u"历史图绘制完成"
plt.show()