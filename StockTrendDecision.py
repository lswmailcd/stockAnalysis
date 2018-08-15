# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import pandas as pd
from sqlalchemy import create_engine

d=10#以步长为d从结束日期向前搜索

def FoundHigh(dt, startPos, step, highPrice):
    curPos = startPos
    i=1
    searchPos = curPos + i
    foundHigh = False
    while i < step:
        if highPrice < data.iloc[searchPos:searchPos+1].values[0, 1]:
            highPrice = data.iloc[searchPos:searchPos+1].values[0, 1]
            curPos = searchPos
            i = 0
            foundHigh = True
        i+=1
        searchPos = curPos + i
    return highPrice, foundHigh, curPos, data.iloc[curPos:curPos+1]


def FoundLow(dt, startPos, step, lowPrice):
    curPos = startPos
    i=1
    searchPos = curPos + i
    foundLow = False
    while i < step:
        if lowPrice > data.iloc[searchPos:searchPos+1].values[0, 3]:
            lowPrice = data.iloc[searchPos:searchPos+1].values[0, 3]
            curPos = searchPos
            i = 0
            foundLow = True
        i+=1
        searchPos = curPos + i
    return lowPrice, foundLow, curPos, data.iloc[curPos:curPos+1]

def decision(h1,h2,l1,l2):
    if h1>h2 and l1>l2:
        return u"上升趋势"
    elif h1<h2 and l1<l2:
        return u"下降趋势"
    else:
        return u"趋势不明"

date = time.strftime('%Y-%m-%d',time.localtime(time.time()))#"2017-11-13"
print "查询证券变化趋势的日期为:",date
engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
data = conn.execute("select code, name from stockindex").fetchall()
nrows = len(data)
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
market = np.array(a, dtype=np.unicode)
b = np.zeros([nrows,2])
trend = np.array(b, dtype=np.unicode)
for i in range(nrows):
    code[i] = data[i][0]
    name[i] = data[i][1].decode('utf8')
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('stockTrendResult')
n=0
worksheet.write(0, n, u"代码")
n+=1
worksheet.write(0, n, u"名称")
n+=1
worksheet.write(0, n, u"趋势1")
n+=1
worksheet.write(0, n, u"趋势2")
n+=2
worksheet.write(0, n, u"趋势1_L1")
n+=2
worksheet.write(0, n, u"趋势1_H1")
n+=2
worksheet.write(0, n, u"趋势1_L2")
n+=2
worksheet.write(0, n, u"趋势1_H2")
n+=3
worksheet.write(0, n, u"趋势2_H1")
n+=2
worksheet.write(0, n, u"趋势2_L1")
n+=2
worksheet.write(0, n, u"趋势2_H2")
n+=2
worksheet.write(0, n, u"趋势2_L2")

totalStock = 0
upTrend = 0
startData = time.strftime('%Y-%m-%d',time.localtime(time.time()-24*60*60*365*2))#起始时间为一年前
endData = time.strftime('%Y-%m-%d',time.localtime(time.time()))
leastEndData = time.strftime('%Y-%m-%d',time.localtime(time.time()-24*60*60*3))
print "查询证券变化趋势的时间段为:%r--%r" %(startData,endData)
for i in range(nrows):
        handle = False
        data = ts.get_hist_data(code[i], start=startData, end=endData)
        worksheet.write(i + 1, 0, code[i])
        worksheet.write(i + 1, 1, name[i])
        try:
            if len(data)>0:
                if data.iloc[0:1].index[0] < leastEndData:
                    worksheet.write(i+1, 2, u"停牌")
                    worksheet.write(i + 1, 3, data.iloc[0:1].index[0])
                elif len(data)<180:
                    worksheet.write(i + 1, 2, u"数据时长不足半年")
                    worksheet.write(i + 1, 3, len(data))
                else:
                    totalStock += 1
                    high1 = data.iloc[0:1].values[0, 1]
                    high1, foundHigh, pos, dH1 = FoundHigh(data, 0, d, high1)
                    if foundHigh:  # 发现了第一个高点，且趋势转为向下，搜索第一个低点
                        low1 = data.iloc[pos:pos + 1].values[0, 3]
                        low1, foundLow, pos, dL1 = FoundLow(data, pos, d, low1)
                        if foundLow:  # 发现了第一个低点，且趋势转为向上，搜索第二个高点
                            high2 = data.iloc[pos:pos + 1].values[0, 1]
                            high2, foundHigh, pos, dH2 = FoundHigh(data, pos, d, high2)
                            if foundHigh:  # 发现了第二个高点，且趋势转为向下，搜索第二个低点
                                low2 = data.iloc[pos:pos + 1].values[0, 3]
                                low2, foundLow, pos, dL2 = FoundLow(data, pos, d, low2)
                                if foundLow:  # 发现了第二个低点，且趋势转为向上，结束搜索
                                    trend[i, 0] = decision(high1, high2, low1, low2)
                                    n = 4
                                    worksheet.write(i + 1, n, dL2.index[0])
                                    n += 1
                                    worksheet.write(i + 1, n, low2)
                                    n += 1
                                    worksheet.write(i + 1, n, dH2.index[0])
                                    n += 1
                                    worksheet.write(i + 1, n, high2)
                                    n += 1
                                    worksheet.write(i + 1, n, dL1.index[0])
                                    n+=1
                                    worksheet.write(i + 1, n, low1)
                                    n += 1
                                    worksheet.write(i + 1, n, dH1.index[0])
                                    n+=1
                                    worksheet.write(i + 1, n, high1)
                    if True:  # 目前为上升趋势，首先查找低点
                        low1 = data.ix[0:1].values[0, 3]
                        low1, foundLow, pos, dL1 = FoundLow(data, 0, d, low1)
                        if foundLow:  # 发现了第一个低点，且趋势转为向上，搜索第一个高点
                            high1 = data.iloc[pos:pos + 1].values[0, 1]
                            high1, foundHigh, pos, dH1 = FoundHigh(data, pos, d, high1)
                            if foundHigh:  # 发现了一个高点，且趋势转为向下，搜索第二个低点
                                low2 = data.iloc[pos:pos + 1].values[0, 3]
                                low2, foundLow, pos, dL2 = FoundLow(data, pos, d, low2)
                                if foundLow:  # 发现了第二个低点，且趋势转为向上，搜索第二个高点
                                    high2 = data.iloc[pos:pos + 1].values[0, 1]
                                    high2, foundHigh, pos, dH2 = FoundHigh(data, pos, d, high2)
                                    if foundHigh:  # 发现了第二个高点，且趋势转为向下，结束搜索
                                        trend[i, 1] = decision(high1, high2, low1, low2)
                                        n = 13
                                        worksheet.write(i + 1, n, dH2.index[0])
                                        n += 1
                                        worksheet.write(i + 1, n, high2)
                                        n += 1
                                        worksheet.write(i + 1, n, dL2.index[0])
                                        n += 1
                                        worksheet.write(i + 1, n, low2)
                                        n += 1
                                        worksheet.write(i + 1, n, dH1.index[0])
                                        n += 1
                                        worksheet.write(i + 1, n, high1)
                                        n += 1
                                        worksheet.write(i + 1, n, dL1.index[0])
                                        n+=1
                                        worksheet.write(i + 1, n, low1)
                    worksheet.write(i + 1, 2, trend[i, 0])
                    worksheet.write(i + 1, 3, trend[i, 1])
                    handle = True
            else:
                worksheet.write(i + 1, 2, u"未获取到数据")
            if handle and trend[i, 0] == u"上升趋势" and trend[i, 1] == u"上升趋势":
                upTrend+=1
                print code[i],name[i],trend[i,0],trend[i,1]
        except Exception, e:
            if(data==None):
                print code[i],name[i],"股票数据无！"
print u"总共检查股票数量%d" %(totalStock),u"上升趋势股票数%d" %(upTrend),u"上升趋势股票占比%.3g%%"%(1.0*upTrend/totalStock*100.0)
workbook.save('.\\data\\stockTrend.xls')





#日期格式YYYYMMDD转为YYYY-MM-DD
def formatDate(Date, formatType='YYYYMMDD'):
    formatType = formatType.replace('YYYY', Date[0:4])
    formatType = formatType.replace('MM', Date[4:6])
    formatType = formatType.replace('DD', Date[-2:])
    return formatType

#df=ts.get_stock_basics()
#code='000002'
#date = df.ix[code]['timeToMarket']  # 上市日期YYYYMMDD
#date=formatDate(str(date),'YYYY-MM-DD')
#dg = ts.get_k_data(code, start=date, end='2016-12-31', autype='hfq')  # 后复权
#print dg.tail(1)