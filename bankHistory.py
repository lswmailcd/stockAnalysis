# -*- coding: utf-8 -*-
import numpy as np
import stockGlobalSpace as sG
import stockTools as sT
import time
from datetime import datetime

startDate = '2019-01-01'
endDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
print "查询开始日期:",startDate
print "查询结束日期:", endDate
sqlString = "select * from bankproductbasics"
conn = sT.createDBConnection()
try:
    ret = conn.execute(sqlString)
except Exception, e:
    print  "连接bankproductbasics数据表失败！"
    exit(1)
product = ret.fetchall()

for p in product:
    sqlString = "select * from bankproductprice where "
    sqlString += "code='%s' and " % (p[0])
    sqlString += "date>='%s' " % (startDate)
    sqlString += "order by date asc limit 1"
    try:
        ret = conn.execute(sqlString)
        stRet = ret.first()
        sPrice = stRet.price
        sDate = stRet.date
    except Exception, e:
        print e
        continue
    sqlString = "select * from bankproductprice where "
    sqlString += "code='%s' and " % (p[0])
    sqlString += "date<='%s' " % (endDate)
    sqlString += "order by date desc limit 1"
    try:
        ret = conn.execute(sqlString)
        endRet = ret.first()
        ePrice = endRet.price
        eDate = endRet.date
    except Exception, e:
        print e
        continue

    daydiff = eDate - sDate
    try:
        profit = (ePrice-sPrice)/sPrice/daydiff.days*365*100
        print p[0],p[1], sDate,eDate,"年化收益率%.3f%%" %(profit)
        print
    except Exception, e:
        print p[0], p[1], "年化收益率获取失败"
        print e
        continue