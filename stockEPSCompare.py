# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
import tushare as ts

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
sqlString = "select code, name, eps from stockprofit_2017_3"
data = conn.execute(sqlString).fetchall()
countInc = 0
count = 0
for i in range(len(data)):
    eps2017_3 = data[i][2]
    sqlString = "select code, name, eps from stockprofit_2016_3 "
    sqlString += "where code="
    sqlString += data[i][0]
    ret = conn.execute(sqlString)
    if ret.rowcount!=0:
        count += 1
        eps2016_3 = ret.first().eps
        if eps2017_3 > eps2016_3 and eps2017_3>0:
            countInc += 1
print count, countInc, float(countInc)/count

