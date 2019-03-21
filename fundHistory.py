# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT
import Graph
import matplotlib.pyplot as plt

code = "110028"
STARTYEAR = 2013  #投资起始年
date = time.strftime('%Y-%m-%d', time.localtime(time.time())) #统计结束时间为当前时间
y,m,d = sT.splitDateString(date)

print u"WARNING:请注意基金历史分红情况，默认以现金分红为准！"
str = raw_input("默认现金分红进行计算请按'回车',如需以红利再投进行计算请按'c',退出请按'q': ")
if str=="q" : exit(0)
stype = "1" #现金分红
if str=="c" :
    stype = "2" #红利再投
print code, u"  计算时间段为：",STARTYEAR,u"年","---",y,u"年",m,u"月"
YEARList = [0]*(y-STARTYEAR+1)
profitList = []
for year in range(STARTYEAR,y+1):
    YEARList[year - STARTYEAR] = year
    startDate = sT.getDateString(year-1, 12, 31)
    saleDate = sT.getDateString(year, 12, 31)
    url = "http://fundex.eastmoney.com/FundWebServices/FundSylCalculator.aspx?fc=" + code
    url = url + "&stime=" + startDate + "&etime=" + saleDate
    url = url + "&stype=" + stype + "&sgfl=" + "0" + "&shfl=" + "0" + "&sg=" + "10000" + "&lx=1"
    data = urllib.urlopen(url).read()
    time.sleep(1)
    infoStr = data.split(':')
    if infoStr[0]=='var Result={"error"':
        print "请检查基金代码是否正确！"
        exit(1)
    rateList = data.split(":")[4].split(",")[0].split('"')
    profitList.append(float(rateList[1])/100.0)
    print year, "%.2f%%" %(profitList[-1]*100.0)

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
Graph.drawColumnChat( ax1, YEARList, profitList, code.decode('utf8'), u'', u'收益率', 20, 0.5, bPercent=True)
plt.show()






