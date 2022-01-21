# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT

sdate = "2020-12-31"
edate = "2021-12-31"

incRate = 0.03

data = xlrd.open_workbook('.\\data\\StockList.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.compat.unicode)
name = np.array(a, dtype=np.compat.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[count] = table.cell(i + 1, 0).value
        name[count] = sT.getStockNameByCode(code[count])
        sname, yearToMarket,_,_ = sT.getStockBasics(code[count])
        if yearToMarket == 0:
            print( code[count], name[count], u"上市时间不详!")
            exit(1)
        sT.checkStockPrice(code[count], sdate,edate)
        count += 1

for i in range(count):
    lstRate = []
    conn = sT.createDBConnection()
    sqlString = "select closeprice, date from stockprice where code={} and date between '{}' and '{}' order by date asc".format(code[i], sdate, edate)
    try:
        ret = conn.execute(sqlString)
    except Exception as e:
        print(e)
        print("stockprice数据表访问错！")
        exit(1)
    r = ret.fetchall()
    if r:
        for k in range(len(r)-1):
            rate = (r[k+1][0]-r[k][0])/r[k][0]
            if rate>incRate: lstRate.append([rate,r[k+1][1]])

        print("{}从{}到{}，涨幅超过{:.0%}的有{}次,占总交易日的{:.2%}".format(name[i], sdate,edate,incRate,len(lstRate),len(lstRate)/260))
        for p in lstRate:   print(p)