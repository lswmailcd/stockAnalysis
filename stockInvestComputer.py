#coding:utf8

import os
import numpy as np
import tushare as ts
import stockTools as sT
import xlrd
import xlwt
import time

style_percent = xlwt.easyxf(num_format_str='0.00%')
style_finance = xlwt.easyxf(num_format_str='￥#,##0.00')

enddate = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
ENDYEAR, ENDMONTH, ENDDAY = sT.splitDateString(enddate)

STARTYEAR, STARTMONTH, STARTDAY = sT.createCalender().getWorkday(-30*6, ENDYEAR, ENDMONTH, ENDDAY) #起始时间为6个月前
startdate = sT.getDateString(STARTYEAR, STARTMONTH, STARTDAY)


data = xlrd.open_workbook('.\\data\\StockAlert.xlsx')
table = data.sheets()[0]
nrows = table.nrows-1
code = []
name = []
count = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="" or table.cell(i + 1, 1).value!="":
        count += 1
        code.append(table.cell(i + 1, 0).value)
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

            sT.checkStockPrice(code[i], sT.getDateString(STARTYEAR, STARTMONTH, STARTDAY), \
                               sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY))

print()
stockList=[]
for i in range(count):
    if code[i] == "" or code[i]=='0.0': continue
    # 查找创新低前的最低点
    priceList=[]
    date = startdate
    pLow, dLow=10000.0, startdate
    closePrice, actDate = 0.0, startdate
    while date <= enddate:
        bFound, closePrice, actDate = sT.getClosePriceBackward(code[i], date)
        if bFound and closePrice<pLow:  pLow, dLow = closePrice, actDate
        date = sT.getDateString(*sT.createCalender().getNextWorkday(date))
    recentPrice, recentDate = closePrice, actDate
    stockList.append((code[i], name[i], pLow, dLow, recentPrice, recentDate, sT.createCalender().dayDiff(dLow,recentDate)))

stockList.sort(reverse=True, key=lambda x:x[-1])
for code, name, pLow, dLow, pCur, dCur, diff in stockList:
    print("{} {}，股票价格最低价{:.2f}元, 日期{}, 当前价{:.2f}元, 日期{}, 最低价距当前日期{}天, 涨幅{:.2%}\n".\
        format(code, name, pLow, dLow, pCur, dCur, diff, (pCur-pLow)/pLow))





