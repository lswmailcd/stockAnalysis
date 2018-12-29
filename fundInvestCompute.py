# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT

STARTYEAR = 2017   #投资起始年
STARTMONTH = 12 #投资起始月份
buyDay = 29      #投资起始日期
ENDYEAR = 2018  #投资结束年
ENDMONTH = 12  #投资结束月份
saleDay = 27  #投资结束日

print u"计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月---",ENDYEAR,u"年",ENDMONTH,u"月"
startDate = sT.getDateString(STARTYEAR, STARTMONTH, buyDay)
saleDate = sT.getDateString(ENDYEAR, ENDMONTH, saleDay)

data = xlrd.open_workbook('.\\data\\data.xls')
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
        name[i] = table.cell(i + 1, 1).value
        count = count+1

workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('dataResult')
for i in range(count):
    foundData = 0
    if code[i] == u'': continue
    url = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=" + code[i]
    url = url + "&page=1&per=20&sdate="
    url = url + startDate
    url = url + "&edate="
    url = url + startDate
    url = url + "&rt=0.19110643402290917"
    data = urllib.urlopen(url).read()
    bs = bs4.BeautifulSoup(data, "html.parser")
    try:
        closePriceStart = float(bs.find_all("td")[1].get_text())
        closePriceAccuStart = float(bs.find_all("td")[2].get_text())
    except Exception, e:
        closePriceAccuStart = 0
        print code[i], name[i], u"没有起始日数据!", startDate

    url = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=" + code[i]
    url = url + "&page=1&per=20&sdate="
    url = url + saleDate
    url = url + "&edate="
    url = url + saleDate
    url = url + "&rt=0.19110643402290917"
    data = urllib.urlopen(url).read()
    bs = bs4.BeautifulSoup(data, "html.parser")
    try:
        closePriceAccuEnd = float(bs.find_all("td")[2].get_text())
    except Exception, e:
        closePriceAccuEnd = 0
        print code[i], name[i], u"没有卖出日数据!", saleDate

    rate = (closePriceAccuEnd - closePriceAccuStart) / closePriceStart
    print code[i], name[i], rate
    worksheet.write(i, 0, code[i])
    worksheet.write(i, 1, name[i])
    worksheet.write(i, 2, rate)
    worksheet.write(i, 3, startDate)
    worksheet.write(i, 4, saleDate)


workbook.save('.\\data\\dataResult.xls')
print "Invest result has been wrotten to dataResult.xls"






