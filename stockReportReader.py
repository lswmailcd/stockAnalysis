#coding:utf-8

from sqlalchemy import create_engine
import numpy as np
import urllib
import bs4
import time
import xlrd
import xlwt
import stockTools as sT

data = xlrd.open_workbook('.\\data\\StockList.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[count] = table.cell(i + 1, 0).value
        name[count] = sT.getStockNameByCode(code[count]).decode('utf8')
        count += 1

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
for i in range(count):
    sqlString = "select timetomarket from stockbasics_20180126 "
    sqlString += "where code="
    sqlString += code[i]
    ret = conn.execute(sqlString)
    result = ret.first()
    if result == None:
        print  code[i], name[i] ,"股票基本数据获取失败！"
        continue
    elif result.timetomarket == 0:
        print  code[i], name[i],"股票上市时间数据为空！"
        continue
    yearToMarket = int(result.timetomarket / 1E4)
    if yearToMarket>STARTYEAR:
        print code[i], name[i],"股票上市时间比起始查询时间晚！"
        continue
    print code[i], name[i], yearToMarket,"年上市！"

url = "http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/"
url += code[i]
url += ".phtml"
data = urllib.urlopen(url).read()
bs = bs4.BeautifulSoup(data, "lxml")