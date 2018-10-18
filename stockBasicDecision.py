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

def getClosePrice(d):
    d=-1
    for i in range(6):
        d = ustr.find("\t",d+1)
    d1=ustr.find("\t",d+1)
    return ustr[d:d1]

discountRate = 0.045
date = "2018-10-18"#time.strftime('%Y-%m-%d',time.localtime(time.time()))#"2017-11-13"
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('stockBasicToday')
worksheet.write(0, 0, u"代码")
worksheet.write(0, 1, u"名称")
worksheet.write(0, 2, u"市盈率")
worksheet.write(0, 3, u"动态年收益")
engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
data = conn.execute("select code,name,stocktype from stockindex where \
                    stocktype='sh_main' or stocktype='sz_main'").fetchall()
stockNum = len(data)
a = np.zeros([stockNum])
price = np.array(a)
eps = np.array(a)
pe = np.array(a)
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
type = np.array(a, dtype=np.unicode)
for i in range(stockNum):
    code[i] = data[i][0]
    name[i] = data[i][1].decode('utf8')
    type[i] = data[i][2].decode('utf8')
    type[i] = type[i][0:2]
normalEnd = True
stockNumValid = 0
start = False
try:
    for i in range(stockNum):
        if start == False and code[i] != "000001":
            continue
        start = True
        found, price[i], _ = st.getClosePrice(code[i], date ) #ts.get_k_data(code[i], start=date, end=date, autype=None)
        if found:
            sqlString = 'select eps from stockprofit_2018_2 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                epsLatest = ret.first().eps
                if epsLatest <=0:
                    continue
            else:
                pe[i] = -1000
                continue
            sqlString = 'select eps from stockprofit_2017_4 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                epsSub1 = ret.first().eps
                if epsSub1 <=0:
                    continue
            else:
                pe[i] = -1000
                continue
            sqlString = 'select eps from stockprofit_2017_2 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                epsSub2 = ret.first().eps
                if epsSub2 <=0:
                    continue
            else:
                pe[i] = -1000
                continue
            eps[i] = epsLatest + epsSub1 - epsSub2
            pe[i] = price[i]/eps[i]
            if pe[i] > 0:
                stockNumValid += 1
                worksheet.write(stockNumValid, 0, code[i])
                worksheet.write(stockNumValid, 1, name[i])
                worksheet.write(stockNumValid, 2, pe[i])
                worksheet.write(stockNumValid, 3,  eps[i])
            #print code[i], name[i], pe[i]
except Exception, e:
    workbook.save('.\\data\\stockBasicToday.xls')
    normalEnd = False
    print "ERROR: stock basic info has been wrotten to excel files partially!"
    print e
if normalEnd:
    workbook.save('.\\data\\stockBasicToday.xls')
    print "stock basic info has been wrotten to excel files"