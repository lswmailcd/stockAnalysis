# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
import tushare as ts
import xlrd
import stockTools as sT
import logRecoder as log

def  deleteDupRow(tablename):#删除重复行并在主键code建立索引
    con = sT.createDBConnection()
    try:
        sqlString = 'alter table '
        sqlString += tablename
        sqlString += ' modify column code char(6)'
        con.execute(sqlString)
        log.writeUtfLog(sqlString.encode('utf8'))

        sqlString = 'alter table '
        sqlString += tablename
        sqlString += ' add column id int(11) PRIMARY KEY AUTO_INCREMENT'
        con.execute(sqlString)
        log.writeUtfLog(sqlString.encode('utf8'))

        sqlString = 'select code, id from '
        sqlString += tablename
        sqlString += ' WHERE id IN (SELECT id FROM (SELECT MAX(id) AS id, COUNT(code) AS ucount FROM '
        sqlString += tablename
        sqlString += ' GROUP BY code HAVING ucount>1 ORDER BY ucount DESC) AS tab)'
        ret = con.execute(sqlString)
        print ret.fetchall()


        sqlString = 'delete from '
        sqlString += tablename
        sqlString += ' WHERE id IN (SELECT id FROM (SELECT MAX(id) AS id, COUNT(code) AS ucount FROM '
        sqlString += tablename
        sqlString += ' GROUP BY code HAVING ucount>1 ORDER BY ucount DESC) AS tab)'
        con.execute(sqlString)
        log.writeUtfLog(sqlString.encode('utf8'))

        sqlString = 'alter table '
        sqlString += tablename
        sqlString += ' DROP column id'
        con.execute(sqlString)
        log.writeUtfLog(sqlString.encode('utf8'))

        sqlString = 'alter table '
        sqlString += tablename
        sqlString += ' add PRIMARY KEY (code)'
        con.execute(sqlString)
        log.writeUtfLog(sqlString.encode('utf8'))
    except Exception, e:
        print e

conn = sT.createDBConnection()
str = "stockbasics_20190118"
#ret=ts.get_report_data(2018,4)
#ret.to_sql("stockreport_2018_4", engine, if_exists='append')
#ret = ts.get_profit_data(2009, 2)
#ret.to_sql('stockprofit_2009_2', engine, if_exists='append')
# ret = ts.get_growth_data(2018, 3)
# ret.to_sql('stockgrowth_2018_3', engine, if_exists='append')
#ret = ts.get_stock_basics()
#ret.to_sql(str,engine,if_exists='append')
# tb = "stockprofit_"
# tb += "%s_%s" % (2018, 3)
# deleteDupRow(tb)
for y in range(2018,2019):
    for i in range(1,4):
        tb = "stockreport_"
        tb += "%s_%s" %(y,i)
        #deleteDupRow(tb)
        # sqlString = "alter table stockreport_sup_"
        # sqlString += "%s_" % (y)
        # sqlString += "%s" % (i)
        # sqlString += " drop dividentime"
        #conn.execute(sqlString)
        #ret=ts.get_report_data(y,i)
        #sqlString = "create table stockreport_sup_"
        #sqlString += "%s_" % (y)
        #sqlString += "%s" % (i)
        #sqlString += "(code char(6) not null primary key,name text,eps_avg double,eps_w double,eps_adj double,"
        #sqlString += "eps_discount double, bvps_bfadj double,bvps_adj double,epcf double,reservedps double,"
        #sqlString += "perundps double,gpr double,roe double,roe_w double,gross_profits double, net_profits_discount double)"
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