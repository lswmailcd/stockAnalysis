# -*- coding: utf-8 -*-
import numpy as np
import stockGlobalSpace as sG
import stockTools as sT
import time
from datetime import datetime

startDate = '2020-12-31'
endDate = '2021-12-31'#time.strftime('%Y-%m-%d', time.localtime(time.time()))#'2019-09-01'
print( "查询开始日期:",startDate)
print( "查询结束日期:", endDate)
sqlString = "select * from bankproductbasics order by no"
conn = sT.createDBConnection()
try:
    ret = conn.execute(sqlString)
except Exception as e:
    print(  "连接bankproductbasics数据表失败！")
    exit(1)
product = ret.fetchall()

for p in product:
    if p[0][:3] != "ZHQ" and p[0][:3] !="GD0": continue
    sqlString = "select * from bankproductprice where "
    sqlString += "code='%s' and " % (p[0])
    sqlString += "date>='%s' " % (startDate)
    sqlString += "order by date asc limit 1"
    try:
        ret = conn.execute(sqlString)
        stRet = ret.first()
        sPrice = stRet.price
        sDate = stRet.date
    except Exception as e:
        print( e)
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
    except Exception as e:
        print( e)
        continue

    daydiff = eDate - sDate
    try:
        profit = (ePrice-sPrice)/sPrice/daydiff.days*365*100
        print( p[0],p[1], sDate,eDate,daydiff.days,"年化收益率%.3f%%" %(profit))
    except Exception as e:
        print( p[0], p[1], "年化收益率获取失败")
        print( e)
        continue