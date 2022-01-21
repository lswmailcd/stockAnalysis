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

STARTYEAR = 2009 #投资起始年
STARTMONTH = 1#投资起始月份
STARTDAY = 5    #投资起始日期

date = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
#DATA2WATCH.append(date)
ENDYEAR, ENDMONTH, ENDDAY = sT.splitDateString(date)

data = xlrd.open_workbook('.\\data\\StockList.xls')
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

for i in range(count):
    if code[i] == "" or code[i]=='0.0': continue
    bFound, closePrice, actDate = sT.getClosePriceForward(code[i], ENDYEAR, ENDMONTH, ENDDAY)
    if bFound and closePrice < price[i]:
        print("{} {}，{} 股票价格{:.2f}元，低于{:.2f}元".format(code[i], name[i], actDate, closePrice, price[i]))






