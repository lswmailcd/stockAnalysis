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

def getClosePrice(d):
    d=-1
    for i in range(6):
        d = ustr.find("\t",d+1)
    d1=ustr.find("\t",d+1)
    return ustr[d:d1]

discountRate = 0.0422
date = time.strftime('%Y-%m-%d',time.localtime(time.time()))#"2017-11-13"
date = "2011-12-30"
print "查询证券价格的日期为:",date
#注意：此程序不要使用MYSQL数据进行查询股票的定义，会使查询股票顺序无法控制！！！！！！！！！！
data = xlrd.open_workbook('.\\data\\data.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
price = np.zeros([nrows])
pe = np.zeros([nrows])
eps = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
market = np.array(a, dtype=np.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[count] = table.cell(i + 1, 0).value
        name[count] = table.cell(i + 1, 1).value
        market[count] = table.cell(i + 1, 2).value
        count += 1
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('stockBasicToday')
worksheet.write(0, 0, u"代码")
worksheet.write(0, 1, u"名称")
worksheet.write(0, 2, u"市盈率")
worksheet.write(0, 3, u"动态年收益")
worksheet.write(0, 4, u"现金流折现值")
normalEnd = True
stockNumValid = 0
stockNum = count
start = False
engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
try:
    for i in range(stockNum):
        if start == False and code[i] != "000001":
            continue
        start = True
        data = ts.get_k_data(code[i], start=date, end=date, autype=None)
        if data.values.size != 0:#if not (u"当天没有数据" in ustr):#
            price[i] = data.values[0, 2]#getClosePrice(ustr)#
            #print code[i], name[i], price[i]
            sqlString = 'select eps from stockprofit_2017_3 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                eps2017_3 = ret.first().eps
                if eps2017_3 <=0:
                    continue
            else:
                pe[i] = -1000
                continue
            #if 0:
            sqlString = 'select eps from stockprofit_2016_4 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
               eps2016_4 = ret.first().eps
               if eps2016_4 <=0:
                  continue
            else:
                pe[i] = -1000
                continue
            sqlString = 'select eps from stockprofit_2016_3 where code=' + code[i]
            ret = conn.execute(sqlString)
            if ret.rowcount!=0:
                eps2016_3 = ret.first().eps
                if eps2016_3 <=0:
                    continue
            else:
                pe[i] = -1000
                continue
            eps[i] = eps2017_3 + eps2016_4 - eps2016_3
            pe[i] = price[i]/eps[i]
            if pe[i] > 0:
                stockNumValid += 1
                worksheet.write(stockNumValid, 0, code[i])
                worksheet.write(stockNumValid, 1, name[i])
                worksheet.write(stockNumValid, 2, pe[i])
                worksheet.write(stockNumValid, 3,  eps[i])
                worksheet.write(stockNumValid, 4, pe[i]*discountRate)
            #print code[i], name[i], pe[i]
except Exception, e:
    workbook.save('.\\data\\stockBasicToday.xls')
    normalEnd = False
    print "ERROR: stock basic info has been wrotten to excel files patially!"
    print e
if normalEnd:
    workbook.save('.\\data\\stockBasicToday.xls')
    print "stock basic info has been wrotten to excel files"