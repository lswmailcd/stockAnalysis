# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
import tushare as ts
import xlrd

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
str = "stockbasics_20190118"
#ret=ts.get_report_data(2019,1)
#ret.to_sql("stockreport_2019_1", engine, if_exists='append')
#ret = ts.get_profit_data(2009, 2)
#ret.to_sql('stockprofit_2009_2', engine, if_exists='append')
# ret = ts.get_growth_data(2018, 3)
# ret.to_sql('stockgrowth_2018_3', engine, if_exists='append')
#ret = ts.get_stock_basics()
#ret.to_sql(str,engine,if_exists='append')
for y in range(2019,2021):
    for i in range(1,5):
        #ret=ts.get_report_data(y,i)
        sqlString = "create table stockreport_sup_"
        sqlString += "%s_" % (y)
        sqlString += "%s" % (i)
        sqlString += "(code char(6) not null primary key,name text,eps_avg double,eps_w double,eps_adj double,"
        sqlString += "eps_discount double, bvps_bfadj double,bvps_adj double,epcf double,reservedps double,"
        sqlString += "perundps double,gpr double,roe double,roe_w double,gross_profits double, net_profits_discount double)"
        #conn.execute(sqlString)
        #str = "stockreport_"
        #str += "%s_" %(y)
        #str += "%s" % (i)
        #ret.to_sql(str, engine, if_exists='append')
for i in range(1):
    year = i+2017
#    ret=ts.get_growth_data(year,4)
    str = "stockgrowth_"
    str += "%s" %(year)

    str += "_4"
#    ret.to_sql(str, engine, if_exists='append')
sqlString = "create table pe_main_20190321(code text, name text, pe double, profit_dynamic double)"
#conn.execute(sqlString)
stock = xlrd.open_workbook('.\\data\\stockBasicToday.xls')
table = stock.sheets()[0]
nrows = table.nrows - 1
for i in range(nrows):
    code = table.cell(i + 1, 0).value
    name = table.cell(i + 1, 1).value
    pe = table.cell(i + 1, 2).value
    profit_dynamic = table.cell(i + 1, 3).value
    sqlString = "insert into pe_main_20190321 values("
    sqlString += "'"
    sqlString += code
    sqlString += "'"
    sqlString += ","
    sqlString += "'"#注意SQL里面需要对code,name使用引号括起来表示字符串，需要在sqlString中加入专门的单引号'code','name'
    sqlString += name
    sqlString += "'"
    sqlString += ","
    sqlString += "%.4f" %(pe)
    sqlString += ","
    sqlString += "%.4f" %(profit_dynamic)
    sqlString += ")"
#    conn.execute(sqlString)