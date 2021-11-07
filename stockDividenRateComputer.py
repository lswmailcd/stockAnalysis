#coding:utf-8

import os
from sqlalchemy import create_engine
import numpy as np
import tushare as ts
import stockTools as sT
import xlrd
import xlwt
import stockDataChecker as ck

date="2014-12-31"
y,m,d = sT.splitDateString(date)
dividenYear = y+1
moneyInvest = 10000.0

print u"***请确保已经使用stockDataChecker.py对数据进行检查***"
str = raw_input("不检查继续请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    dirName = os.path.dirname(os.path.realpath(__file__))
    #ck.process(2008, 2017, "sh50.xls" )
    os.system('C:\Users\lsw\Anaconda3\envs\conda27\python ' + dirName + '\\stockDataChecker.py 2008 2017 highdividen.xls')

year, month, day =sT.splitDateString(date)
data = xlrd.open_workbook('.\\data\\highdividen.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
weight = np.array(a, dtype=np.float)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[i] = table.cell(i + 1, 0).value
        if code[i] == "" or code[i]=='0.0': continue
        name[i] = sT.getStockNameByCode(code[i]).decode('utf8')
        sname, yearToMarket,_,_ = sT.getStockBasics(code[i])
        if yearToMarket == 0:
            print code[i], name[i], u"上市时间不详!"
            exit(1)
        weight[i] = table.cell(i + 1, 2).value/100.0

conn = sT.createDBConnection()
nStock = 0.0
dividenTotal = 0.0
for i in range(nrows):
    if code[i] == "" or code[i]=='0.0':
        continue
    found, price, m, d = sT.getClosePriceForward(code[i], date)
    if found:
        nStock = moneyInvest*weight[i]/price
        print code[i], name[i], "nStock=",nStock, "Price=",price
    else:
        print code[i], name[i], "价格获取失败！"

    distribYear = dividenYear
    bDividen = True
    try:
        sqlString = "select distrib from stockreport_"
        sqlString += "%s" % (distribYear)
        sqlString += "_4 where code="
        sqlString += code[i]
        ret = conn.execute(sqlString)
    except Exception, e:
        print "ERROR: ", code[i], name[i], "connect database failure!"
        print e
        exit(1)
    resultDistrib = ret.first()
    if resultDistrib is None or resultDistrib.distrib is None:
        print "WARNING:", code[i], name[i], distribYear, u"年分红不详，数据库年报分红数据获取失败！此年可能无分红！"
        bDividen = False  # 无分红
    else:
        # 计算分红送转
        r, s = sT.getDistrib(resultDistrib.distrib, distribYear)
        dividenTotal += r*nStock
        print code[i], name[i], "distrib=",r,"股息率: %.2f%%" %(r/price*100.0)

print u"总计股息：","%.2f" %(dividenTotal), u"股息率:","%.2f%%" %(dividenTotal/moneyInvest*100.0)
