#coding:utf8

import os
from sqlalchemy import create_engine
import numpy as np
import tushare as ts
import stockTools as sT
import xlrd
import xlwt
import stockDataChecker as ck

date="2019-01-03"
dividenYear = 2017

print u"***请确保已经使用stockDataChecker.py对数据进行检查***"
str = raw_input("不检查继续请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    dirName = os.path.dirname(os.path.realpath(__file__))
    ck.process(2008, 2017, "sh50.xls" )
    #os.system('C:\Users\lsw\Anaconda3\envs\conda27\python ' + dirName + '\\stockDataChecker.py 2008 2017 sh50.xls')

year, month, day =sT.splitDateString(date)
data = xlrd.open_workbook('.\\data\\sh50.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[i] = table.cell(i + 1, 0).value
        if code[i] == "" or code[i]=='0.0': continue
        name[i] = sT.getStockNameByCode(code[i]).decode('utf8')
        sname, yearToMarket = sT.getStockBasics(code[i])
        if yearToMarket == 0:
            print code[i], name[i], u"上市时间不详!"
            exit(1)

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
priceTotal = 0.0
dividenTotal = 0.0
for i in range(nrows):
    if code[i] == "" or code[i]=='0.0':
        exit(1)
    found, price, _, _ = sT.getClosePrice(code[i], date)
    if found:
        priceTotal += price
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
        r, s = sT.getDistrib(resultDistrib.distrib)
        dividenTotal += r
        #print code[i], name[i], r

print dividenTotal, priceTotal
print dividenTotal/priceTotal