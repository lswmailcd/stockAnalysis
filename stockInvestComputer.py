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

startdate = time.strftime('%Y-%m-%d',time.localtime(time.time()-24*60*60*90))#起始时间为6个月前
STARTYEAR, STARTMONTH, STARTDAY = sT.splitDateString(startdate)

enddate = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
ENDYEAR, ENDMONTH, ENDDAY = sT.splitDateString(enddate)

data = xlrd.open_workbook('.\\data\\StockAlert.xlsx')
table = data.sheets()[0]
nrows = table.nrows-1
code = []
name = []
price = []
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
            price.append(table.cell(i + 1, 2).value)
            sname, yearToMarket,_ ,_ = sT.getStockBasics(code[i])
            if yearToMarket == 0:
                print( code[i], name[i], u"上市时间不详!")
                exit(1)

            sT.checkStockPrice(code[i], sT.getDateString(STARTYEAR, STARTMONTH, STARTDAY), \
                               sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY))

print()
for i in range(count):
    if code[i] == "" or code[i]=='0.0': continue
    # 查找创新低前的最低点
    priceList=[]
    date = startdate

    while date <= enddate:
        bFound, closePrice, actDate = sT.getClosePriceBackward(code[i], date)
        if bFound: priceList.append((closePrice, actDate))
        date = sT.getDateString(*sT.createCalender().getNextWorkday(date))
    recentPrice, recentDate = priceList[-1]
    priceList.sort()
    print("{} {}，股票价格最低价{:.2f}元, 日期{}, 当前价{:.2f}元, 日期{}, 最低价距当前日期{}天".\
        format(code[i], name[i], priceList[0][0], priceList[0][1],recentPrice, recentDate, sT.createCalender().dayDiff(priceList[0][1],recentDate) ))






