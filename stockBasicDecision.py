# -*- coding: utf-8 -*-
import urllib
import random
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import pandas as pd
from sqlalchemy import create_engine
import stockTools as st

discountRate = 0.0395
date = "2021-11-03"#time.strftime('%Y-%m-%d',time.localtime(time.time()))#"2017-11-13"
filename = '.\\data\\stockPETTM.xls'
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet(date)
worksheet.write(0, 0, u"代码")
worksheet.write(0, 1, u"名称")
worksheet.write(0, 2, u"市盈率")
worksheet.write(0, 3, u"动态年收益")
engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
data = conn.execute("select code,name from stockbasics where code like '600%%'\
                     or code like '601%%' or code like '000%%' or code like '001%%'").fetchall()
stockNum = len(data)
code = []
name = []
for i in range(stockNum):
    code.append(data[i][0])
    name.append(data[i][1])
normalEnd = True
stockNumValid = 0
start = False
try:
    for i in range(stockNum):
        if start == False and code[i] != "000001":
            continue
        st.checkStockPrice(code[i], date, date)
        start = True
        found, price = st.getClosePrice(code[i], date )
        #print(code[i],name[i])
        if found:
            sqlString = 'select eps from stockprofit_2020_3 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                epsSub2 = ret.first().eps
                if epsSub2 <= 0: continue
            else:
                pe = -1000
                continue
            sqlString = 'select eps from stockprofit_2020_4 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                epsSub1 = ret.first().eps
                if epsSub1 <= 0: continue
            else:
                pe = -1000
                continue
            sqlString = 'select eps from stockprofit_2021_3 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                epsLatest = ret.first().eps
                if epsLatest <= 0: continue
            else:
                pe = -1000
                continue
            eps = epsLatest + epsSub1 - epsSub2
            pe = price/eps
            if pe > 0:
                stockNumValid += 1
                worksheet.write(stockNumValid, 0, code[i])
                worksheet.write(stockNumValid, 1, name[i])
                worksheet.write(stockNumValid, 2, pe)
                worksheet.write(stockNumValid, 3,  eps)
except Exception as e:
    workbook.save(filename)
    normalEnd = False
    print("ERROR: stock basic info has been wrotten to excel file partially!")
    print(e)
if normalEnd:
    workbook.save(filename)
    print("stock basic info has been wrotten to excel file.")