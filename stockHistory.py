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
date = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
y, m, d = sT.splitDateString(date)
if m<5: #y-1年的年报还没有出来
    YEAREND = y-2
else:
    YEAREND = y-1

name, yearToMarket, _, _ = sT.getStockBasics(code)
if yearToMarket == 0:
    print code, name, u"上市时间不详!"
    exit(1)
if yearToMarket>=YEARSTART: YEARSTART = yearToMarket+1
str = raw_input("不检查历史数据继续请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    print "checking asset_debt..."
    if sT.checkStockAssetDebt(code, YEARSTART, y-1) == False: exit(1)
    print "checking reports..."
    found, YEARSTART = sT.checkStockReport(code, YEARSTART, y-1)
    if found==False : exit(1)
    print "checking distrib..."
    if sT.checkDistrib(code, YEARSTART, YEAREND) == False: exit(1)
    print "checking DONE!"

YEARList = [0]*(y-YEARSTART+1)
PEList = [0]*(y-YEARSTART+1)
PriceList = [0]*(y-YEARSTART+1)
#DividenList = [0]*(YEAREND-YEARSTART+1)
#PBList = [0]*(YEAREND-YEARSTART+1)
EPS=0.0
#BPS=0.0
closePrice=0.0
netProfits=0.0
for year in range(YEARSTART, YEAREND+1):
    YEARList[year - YEARSTART] = year
    sqlString = "select eps,net_profits,bvps from stockreport_"
    sqlString += "%s" %(year)
    sqlString += "_4 where code="
    sqlString += code
    conn = sT.createDBConnection()
    ret = conn.execute(sqlString)
    result = ret.first()
    if result is None or result.eps is None:
        print year,u"年，数据库数据获取失败！"
        continue
    foundData = False
    for month in range(12,0,-1):
        if foundData==True:
            break
        for day in range(31,0,-1):
            if not sT.validDate(month,day):
                continue
            date = sT.getDateString(year,month,day)
            data = ts.get_k_data(code, start=date, end=date, autype=None)
            if data.empty == False:
                foundData = True
                closePrice = data.values[0, 2]
                EPS = result.eps
                #ROE = result.roe
                BPS = result.bvps
                netProfits = result.net_profits
                if not abs(EPS)<0.001:
                    PEList[year - YEARSTART] = closePrice / EPS
                    PriceList[year - YEARSTART] = closePrice * sT.getStockCount(code, year, 4) #得到当年总市值
                else:
                    print code,name,year,u"年EPS为0"
                #if BPS is not None:
                #    PBList[year - YEARSTART] = closePrice / BPS
                #else:
                #    print code, name, year, "年BPS为0"
                #print year, closePrice, result.eps, PEList[year - YEARSTART]
                break

#获得该年报没有出来前的动态PE
date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
#计算动态PE
y, m, d = sT.splitDateString(date)
if m<5:#y-1年的年报没有出来，使用滚动EPS计算y-1和y年的PETTM
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' % (y-1)
    sqlString += '_3 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q3 = result.eps
            print y-1, 'Q3', eps_Q3
        else:
            print y-1, u"年3季度eps数据缺失！"
            exit(1)
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' % (y-2)
    sqlString += '_4 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q4_LastYear = result.eps
            print y-2, 'Q4', eps_Q4_LastYear
        else:
            print y-2, u"年4季度eps数据缺失！"
            exit(1)
        sqlString = 'select eps from stockreport_'
        sqlString += '%s' % (y-2)
        sqlString += '_3 where code='
        sqlString += code
        ret = conn.execute(sqlString)
        if ret is not None:
            result = ret.first()
            if result is not None:
                eps_Q3_LastYear = result.eps
                print y-2, 'Q3', eps_Q3_LastYear
            else:
                print y-2, u"年3季度eps数据缺失！"
                exit(1)
        EPS = eps_Q3 + eps_Q4_LastYear - eps_Q3_LastYear
        #记录y-1年的数据
        f, closePrice,_,_ = sT.getClosePriceForward(code, y-1,12,31)
        PEList[y-1 - YEARSTART] = round(closePrice / EPS, 2)
        YEARList[y-1 - YEARSTART] = y-1
        nStockTotal = sT.getStockCount(code, y-1, 3)
        PriceList[y-1 - YEARSTART] = closePrice * nStockTotal
elif m<9:#y年的2季报没有出来
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' %(y)
    sqlString += '_1 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q1 = result.eps
            print y,'Q1', eps_Q1
        else:
            print y,u"年1季度eps数据缺失！"
            exit(1)
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' %(y-1)
    sqlString += '_4 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q4_LastYear = result.eps
            print y-1, 'Q4', eps_Q4_LastYear
        else:
            print y-1,u"年4季度eps数据缺失！"
            exit(1)
        sqlString = 'select eps from stockreport_'
        sqlString += '%s' % (y - 1)
        sqlString += '_1 where code='
        sqlString += code
        ret = conn.execute(sqlString)
        if ret is not None:
            result = ret.first()
            if result is not None:
                eps_Q1_LastYear = result.eps
                print y-1, 'Q1', eps_Q1_LastYear
            else:
                print y-1, u"年1季度eps数据缺失！"
                exit(1)
            EPS = eps_Q4_LastYear + eps_Q1 - eps_Q1_LastYear
            f, closePrice, _, _ = sT.getClosePriceForward(code, y - 1, 12, 31)
            nStockTotal = sT.getStockCount(code, y, 1)
            PriceList[y - 1 - YEARSTART] = closePrice * sT.getStockCount(code, y-1, 4)
elif m<11:#3季报没有出来
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' %(y)
    sqlString += '_2 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q2 = result.eps
            print y, 'Q2', eps_Q2
        else:
            print y,u"年2季度eps数据缺失！"
            exit(1)
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' %(y-1)
    sqlString += '_4 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q4_LastYear = result.eps
            print YEAREND-1, 'Q4', eps_Q4_LastYear
        else:
            print y,u"年4季度eps数据缺失！"
            exit(1)
        sqlString = 'select eps from stockreport_'
        sqlString += '%s' % (y - 1)
        sqlString += '_2 where code='
        sqlString += code
        ret = conn.execute(sqlString)
        if ret is not None:
            result = ret.first()
            if result is not None:
                eps_Q2_LastYear = result.eps
                print y - 1, 'Q2', eps_Q2_LastYear
            else:
                print y-1, u"年2季度eps数据缺失！"
                exit(1)
        EPS = eps_Q4_LastYear + eps_Q2 - eps_Q2_LastYear
        f, closePrice, _, _ = sT.getClosePriceForward(code, y - 1, 12, 31)
        nStockTotal = sT.getStockCount(code, y, 2)
        PriceList[y - 1 - YEARSTART] = closePrice * sT.getStockCount(code, y - 1, 4)
else :#3季报出来了
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' %(y)
    sqlString += '_3 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q3 = result.eps
            print y, 'Q3', eps_Q3
        else:
            print y,u"年3季度eps数据缺失！"
            exit(1)
    sqlString = 'select eps from stockreport_'
    sqlString += '%s' %(y-1)
    sqlString += '_4 where code='
    sqlString += code
    ret = conn.execute(sqlString)
    if ret is not None:
        result = ret.first()
        if result is not None:
            eps_Q4_LastYear = result.eps
            print y-1, 'Q4', eps_Q4_LastYear
        else:
            print y-1,u"年4季度eps数据缺失！"
            exit(1)
        sqlString = 'select eps from stockreport_'
        sqlString += '%s' % (y - 1)
        sqlString += '_3 where code='
        sqlString += code
        ret = conn.execute(sqlString)
        if ret is not None:
            result = ret.first()
            if result is not None:
                eps_Q3_LastYear = result.eps
                print y - 1, 'Q3', eps_Q3_LastYear
            else:
                print y-1, u"年3季度eps数据缺失！"
                exit(1)
        EPS = eps_Q3 + eps_Q4_LastYear - eps_Q3_LastYear
        f, closePrice, _, _ = sT.getClosePriceForward(code, y - 1, 12, 31)
        nStockTotal = sT.getStockCount(code, y, 3)
        PriceList[y - 1 - YEARSTART] = closePrice * sT.getStockCount(code, y - 1, 4)
#记录第y年的数据
f, closePrice,_,_  = sT.getClosePriceForward(code, date)
PEList[y - YEARSTART] = round(closePrice / EPS,2)
YEARList[y - YEARSTART] = y
PriceList[y - YEARSTART] = closePrice * nStockTotal
#PBList[YEAREND - YEARSTART] = closePrice/BPS
#print YEAREND, closePrice, EPS, PEList[YEAREND - YEARSTART]
for i in range(y - YEARSTART + 1):
    PriceList[i] = PriceList[i]/10**4

fig = plt.figure()
ax1 = fig.add_subplot(2,1,1,xlim=(YEARSTART-1, y+1), ylim=(-4, 4))
ax2 = fig.add_subplot(2,1,2,xlim=(YEARSTART-1, y+1), ylim=(-4, 4))
#ax3 = fig.add_subplot(3,1,3,xlim=(YEARSTART-1, YEAREND+1), ylim=(-4, 4))
Graph.drawColumnChat( ax1, YEARList, PriceList, name.decode('utf8'), u'', u'总市值(亿元)', 20, 0.5,True)
Graph.drawColumnChat( ax2, YEARList, PEList, u'', u'', u'PE_TTM', 20, 0.5)
#Graph.drawColumnChat( ax3, YEARList, PBList, u'', u'', u'PB', 20, 0.5)
print code,name,u"历史图绘制完成"
plt.show()