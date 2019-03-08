# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT

STARTYEAR = 2019   #投资起始年
STARTMONTH = 1 #投资起始月份
buyDay = 1      #投资起始日期
ENDYEAR = 2019  #投资结束年
ENDMONTH = 3  #投资结束月份
saleDay = 3  #投资结束日

print u"WARNING:请注意基金历史分红情况，默认以现金分红为准！"
str = raw_input("默认现金分红进行计算请按'回车',如需以红利再投进行计算请按'c',退出请按'q': ")
if str=="q" : exit(0)
stype = "1" #现金分红
if str=="c" :
    stype = "2" #红利再投
print u"计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月", buyDay,u"日\
---",ENDYEAR,u"年",ENDMONTH,u"月", saleDay,u"日"
startDate = sT.getDateString(STARTYEAR, STARTMONTH, buyDay)
saleDate = sT.getDateString(ENDYEAR, ENDMONTH, saleDay)
data = xlrd.open_workbook('.\\data\\etfdata.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
discount = np.array(a, dtype=np.float)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[i] = table.cell(i + 1, 0).value
        if code[i] == "" or code[i]=='0.0': continue
        name[i] = table.cell(i + 1, 1).value
        discount[i] = table.cell(i + 1, 2).value
        count = count+1

workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('dataResult')
for i in range(count):
    foundData = 0
    if code[i] == u'' : continue
    url = "http://fundex.eastmoney.com/FundWebServices/FundSylCalculator.aspx?fc=" + code[i]
    url = url + "&stime=" + startDate + "&etime=" + saleDate
    url = url + "&stype=" + stype + "&sgfl=" + "0" + "&shfl=" + "0" + "&sg=" + "10000" + "&lx=1"
    data = urllib.urlopen(url).read()
    time.sleep(1)
    infoStr = data.split(':')
    if infoStr[0]=='var Result={"error"':
        print data
        continue
    rateList = data.split(":")[4].split(",")[0].split('"')
    rate = float(rateList[1])/100.0
    worksheet.write(i, 0, code[i])
    worksheet.write(i, 1, name[i])
    worksheet.write(i, 2, rate)
    worksheet.write(i, 3, startDate)
    worksheet.write(i, 4, saleDate)
    print code[i],name[i], "%.2f%%" %(rate*100.0)

workbook.save('.\\data\\dataResult.xls')
print "Invest result has been wrotten to dataResult.xls"






