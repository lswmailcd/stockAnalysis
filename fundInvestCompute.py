# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT

style_percent = xlwt.easyxf(num_format_str='0.00%')

STARTYEAR = 2021  #投资起始年
STARTMONTH = 2 #投资起始月份
startDay = 26      #投资起始日期
ENDYEAR = 2021 #投资结束年
ENDMONTH = 3  #投资结束月份
endDay = 31  #投资结束日


print u"WARNING:请注意基金历史分红情况，默认以现金分红为准！"
str = raw_input("默认红利再投进行计算请按'回车',如需以现金分红进行计算请按'c',退出请按'q': ")
if str=="q" : exit(0)
stype = "1" #红利再投
if str=="c" :
    stype = "2" #现金分红
print u"一次性投资计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月", startDay,u"日\
---",ENDYEAR,u"年",ENDMONTH,u"月", endDay,u"日"
startDate = sT.getDateString(STARTYEAR, STARTMONTH, startDay)
saleDate = sT.getDateString(ENDYEAR, ENDMONTH, endDay)
data = xlrd.open_workbook('.\\data\\fundata.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 1).value != "":
        code[i] = table.cell(i + 1, 0).value
        name[i] = table.cell(i + 1, 1).value
        count += 1

workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('dataResult')
worksheet.write(0, 0, u"代码")
worksheet.write(0, 1, u"名称")
worksheet.write(0, 2, u"收益率")
worksheet.write(0, 3, u"年化收益率")
worksheet.write(0, 4, u"起始时间")
worksheet.write(0, 5, u"终止时间")
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
    investPeriod = round(sT.createCalender().dayDiff(STARTYEAR,STARTMONTH,1,ENDYEAR,ENDMONTH,endDay)/365.0, 2)
    ratePerYear = round(((rate + 1) ** (1.0 / investPeriod) - 1), 4)
    worksheet.write(i+1, 0, code[i])
    worksheet.write(i+1, 1, name[i])
    worksheet.write(i+1, 2, rate, style_percent)
    worksheet.write(i+1, 3, ratePerYear, style_percent)
    worksheet.write(i+1, 4, startDate)
    worksheet.write(i+1, 5, saleDate)
    print code[i], name[i], "收益：%.2f%%" % (rate * 100.0), "年化收益：%.2f%%" % (ratePerYear * 100.0)

workbook.save('.\\data\\dataResult.xls')
print "Invest result has been wrotten to dataResult.xls"





