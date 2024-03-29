#coding:utf8

import os
import numpy as np
import tushare as ts
import stockTools as sT
import stockDataChecker as ck
import xlrd
import xlwt
import time
import Graph as g
import matplotlib.pyplot as plt

#60天以上不创新低表示可能下降趋势结束

style_percent = xlwt.easyxf(num_format_str='0.00%')
style_finance = xlwt.easyxf(num_format_str='￥#,##0.00')

enddate = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
ENDYEAR, ENDMONTH, ENDDAY = sT.splitDateString(enddate)
ENDYEAR, ENDMONTH, ENDDAY = sT.createCalender().getWorkdayForward(ENDYEAR, ENDMONTH, ENDDAY) #得到交易日
enddate = sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY)

nWeeks = 4*6
startdateList, endateList=[],[]
n = 0
y, m, d = ENDYEAR, ENDMONTH, ENDDAY
STARTYEAR, STARTMONTH, STARTDAY = ENDYEAR, ENDMONTH, ENDDAY
while n<nWeeks:
    endateList.insert(0, sT.getDateString(y, m, d))
    STARTYEAR, STARTMONTH, STARTDAY = sT.createCalender().getWorkday(-30 * 6, y, m, d)  # 起始时间为6个月前
    startdateList.insert(0, sT.getDateString(STARTYEAR, STARTMONTH, STARTDAY))
    y, m, d = sT.createCalender().getWorkday(-7, y, m, d)
    n+=1

data = xlrd.open_workbook('.\\data\\StockAlert.xlsx')
table = data.sheets()[0]
nrows = table.nrows-1
code = []
name = []
count = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="" or table.cell(i + 1, 1).value!="":
        count += 1
        type = table.cell_type(i + 1, 0)
        if type==2:#number
            value = str(int(table.cell(i + 1, 0).value))
        elif type==1:#string
            value = table.cell(i + 1, 0).value
        value = '0'*(6-len(value))+value
        code.append(value)
        if code[i] == "":
            name.append("")
        else:
            name.append(sT.getStockNameByCode(code[i]))
            if name[i] == None:
                code[i] = ""
                continue
            sname, yearToMarket,_ ,_ = sT.getStockBasics(code[i])
            if yearToMarket == 0:
                print( code[i], name[i], u"上市时间不详!")
                exit(1)

            ck.subprocess(code[i], STARTYEAR, ENDYEAR)

print()
percentList=[]
stockTurnover=[]
for startdate, enddate in zip(startdateList,endateList):
    stockList=[]
    for i in range(count):
        if code[i] == "" or code[i]=='0.0': continue
        # 查找创新低前的最低点
        date = startdate
        pLow, dLow=10000.0, startdate
        closePrice, actDate = 0.0, startdate
        priceList=[]
        if not sT.getClosePriceList( code[i], priceList, startdate, enddate ): continue
        if enddate == endateList[-1]:
            _,v0,d0 = priceList[0]
            for _,v,d in priceList:
                if v/v0>3.0: stockTurnover.append((code[i], name[i], d))
                v0 = v
        recentPrice, recentVol, recentDate = priceList[-1]
        priceList.sort()
        pLow, vLow, dLow = priceList[0]
        stockList.append((code[i], name[i], pLow, vLow, dLow, recentPrice, recentVol, recentDate, sT.createCalender().dayDiff(dLow,recentDate)))

    stockList.sort(reverse=True, key=lambda x:x[-1])
    n, m = 0, 0
    for c, na, pLow, vLow, dLow, pCur, vCur, dCur, diff in stockList:
        if diff>60: n+=1
        if diff<15: m+=1
        if  enddate == endateList[-1]:
            print("{} {}，股票价格最低价{:.2f}元, 日期{}, 当前价{:.2f}元, 日期{}, 最低价距当前日期{}天, 涨幅{:.2%}".\
                format(c, na, pLow, dLow, pCur, dCur, diff, (pCur-pLow)/pLow))
            print("换手率是前一交易日3倍以上：",end="")
            for stock in stockTurnover:
                if c==stock[0]: print(stock[2],end=" ")
            print('\n')
    if enddate == endateList[-1]:   print("下降趋势结束(>60天不创新低)股票占比{:.2%},两周内(<15天)创新低股票占比{:.2%}".\
                                          format(n/len(stockList), m/len(stockList)))
    percentList.append((enddate,n/len(stockList), m/len(stockList)))

title="{}至{}股票组合下降趋势统计图".format(endateList[0], endateList[-1])
yScale = 10
xList = [x[0] for x in percentList]
yList=[[x[2]for x in percentList], [x[1]for x in percentList]]
#print(yList[0])
name=["两周内(<15天)创新低股票占比","下降趋势结束(>60天不创新低)股票占比"]
g.drawRateChat(xList, yList, name, title)




