#coding:utf8

from sqlalchemy import create_engine
import numpy as np
import Graph
import tushare as ts
import time
import matplotlib.pyplot as plt
import stockTools as sT
import xlrd
import xlwt

YEAREND = 2017  #统计结束时间
PERIODE = 8 #计算股票的时间段
YEARSTART = YEAREND-PERIODE+1  #统计起始时间

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
sqlString = "select code,name,timetomarket from stockbasics_20180428"
ret = conn.execute(sqlString)
nrow = ret.rowcount
data = ret.fetchall()
a = np.zeros([nrow])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
market = np.array(a, dtype=np.unicode)
count=0
try:
    for i in range(nrow):
        code[count] = data[i][0]
        if code[count] < "300000":continue
        if sT.getMarketType(code[count]) not in("sz_cyb"):continue
        name[count] = data[i][1].decode('utf8')
        timeToMarket = data[i][2]
        marketYear = int(timeToMarket/10**4)
        if marketYear > YEARSTART:
            print code[count], name[count], "上市时间过短！"
            continue
        count += 1

    workbook = xlwt.Workbook(encoding = 'ascii')
    worksheet = workbook.add_sheet('PEHistory')
    worksheet.write(0, 0, u"代码")
    worksheet.write(0, 1, u"名称")
    j = 0
    for year in range(YEAREND,YEARSTART-1,-1):
        worksheet.write(0, j+2, year)
        j += 1
    idx = 0
    for i in range(count):
        YEARList = [0]*(YEAREND-YEARSTART+1)
        PEList = [1000]*(YEAREND-YEARSTART+1)
        EPS=0.0
        closePrice=0.0
        netProfits=0.0
        for year in range(YEAREND,YEARSTART-1,-1):
            YEARList[YEAREND-year] = year
            sqlString = "select eps,net_profits from stockreport_"
            sqlString += "%s" %(year)
            sqlString += "_4 where code="
            sqlString += code[i]
            ret = conn.execute(sqlString)
            result = ret.first()
            if result is None or result.eps is None:
                print code[i],name[i],year,"年，数据库数据获取失败！"
                continue
            found,closePrice,d = sT.getClosePriceForward(code[i], year, 12, 31)
            if found:
                EPS = result.eps
                netProfits = result.net_profits
                if EPS > 0 : PEList[YEAREND-year] = closePrice / EPS
                else:continue
            else:
                print code[i],name[i],year,"年，收盘价获取失败！"

        minPE = np.min(PEList)
        maxPE = np.max(PEList)
        if np.abs(minPE-PEList[0])<0.01:
            print code[i], name[i],"符合条件！"
            worksheet.write(idx + 1, 0, code[i])
            worksheet.write(idx + 1, 1, name[i])
            for k in range(YEAREND-YEARSTART+1):
                worksheet.write(idx + 1, k+2, PEList[k])
            idx += 1
            if idx > 50:
                raise Exception("excel文件记录大于50！")
except Exception,e:
    workbook.save('.\\data\\PEHistory.xls')
    print e
    print "PE history have been partially wrotten to PEHistory.xls"
    exit(1)
workbook.save('.\\data\\PEHistory.xls')
print "PE history have been wrotten to PEHistory.xls"
print "请确认已使用stockDataChecker.py进行数据检查！"