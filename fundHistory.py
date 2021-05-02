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
import matplotlib as mpl
from random import randint
import stockGlobalSpace as sG
import datetime

BONUS_SHARE = "1" #红利再投
BONUS_CASH = "2" #现金红利

#!!!!注意，一定要保证所有日期处于日历日期内，否则程序会报错！！！
STARTYEAR = 2020 #投资起始年
STARTMONTH = 12 #投资起始月份
STARTDAY = 1      #投资起始日期

#定投结束日即是卖出日，目前无法实现定投结束日和卖出日不同。
ENDYEAR = 2021  #定投结束年
ENDMONTH = 4 #定投结束月份
ENDDAY = 30  #定投结束日
BUYDAY = 10 #定投日
INTERVAL  = 1    #定投间隔的月份
INVESTMONEY = "10000"

data = xlrd.open_workbook('.\\data\\fundata.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.compat.unicode)
name = np.array(a, dtype=np.compat.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[i] = table.cell(i + 1, 0).value
        if code[i] == "" or code[i]=='0.0': continue
        count = count+1

print( u"WARNING:请注意基金历史分红情况，默认为红利再投资！")
str = input("默认红利再投进行计算请按'回车',如需现金分红以进行计算请按'c',退出请按'q': ")
if str=="q" : exit(0)
stype = BONUS_SHARE #红利再投
if str=="c" :
    stype = BONUS_CASH #现金分红

str = input("如不进行分红检查请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    print("开始检查基金分红数据......")
    for i in range(count):
        if code[i] == u'': continue
        sT.checkFundDistrib(code[i])
    print("基金分红数据检查完成！")

print( u"定投计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月", STARTDAY,u"日\
---",ENDYEAR,u"年",ENDMONTH,u"月", ENDDAY,u"日")

startDate = sT.getDateString(STARTYEAR, STARTMONTH, STARTDAY)
endDate = sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY)

dataList=[]
for i in range(count):
    url = "http://fund.eastmoney.com/data/FundInvestCaculator_AIPDatas.aspx?fcode=" + code[i]
    url = url + "&sdate=" + startDate + "&edate=" + endDate + "&shdate=" + endDate
    url = url + "&round=" + "%s" % (INTERVAL) + "&dtr=" + "%s" % (BUYDAY) + "&p=" + "0" + "&je=" + INVESTMONEY
    url = url + "&stype=" + stype + "&needfirst=" + "2" + "&jsoncallback=FundDTSY.result"
    response = urllib.request.urlopen(url=url)
    data = response.read().decode("utf8")
    time.sleep(randint(1, 3))
    infoStr = data.split('|')
    name[i] = infoStr[1]
    if infoStr[2] == '0期':
        print( code,infoStr[1],data)
        exit(1)

    dictColumnValues = {}
    investTotal = float(infoStr[3].replace(",", ""))
    totalValue = float(infoStr[5].replace(",", ""))
    details = infoStr[7][:-3].split("_")

    dateList=[]
    rateList=[]
    moneyTotal, shareTotalInvest, shareTotal, diffWorst, diffBest, dateWorse, dateBest, diffWorstRate, diffBestRate, \
    rateWorst, rateBest, dateRateWorst, dateRateBest, bonusTotal, lostWorst, earnBest = \
        0.0, 0.0, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, 0.0
    d0 = startDate
    # 获取基金分红数据，用于计算份额变动（红利再投）或分红情况（现金红利）
    _, distrib = sT.getFundDistrib(code[i])
    for s in details:
        t = s.split("~")  # t[0]:日期,t[1]:价格,t[2]:本金,t[3]:份额
        p = t[0].replace(",", "").find("星")
        date = t[0].replace(",", "")[:p]
        dateList.append(date)
        share = float(t[3].replace(",", ""))
        shareTotalInvest += share
        shareTotal += share
        for d in distrib:  # d[0]:登记及除息日，d[1]:每份分红金额,d[2]:红利发放日，红利再投资日
            if d0 <= d[0] < date:
                disMoney = shareTotal * d[1]
                if stype == BONUS_SHARE:  # 红利再投
                    shareTotal += disMoney / sT.getFundPrice(code[i], d[2])[1]
                else:  # 现金红利
                    bonusTotal += disMoney

        d0 = date

        moneyTotal = moneyTotal + float(t[2].replace(",", ""))
        diff = float(t[1]) * shareTotal - moneyTotal
        rate = diff / moneyTotal
        rateList.append(rate*100.0)

    #print((dateList)
    dataList.append([dateList,rateList])

for i in range(len(dataList)):#日期选择一个日期，坐标轴不能有两种不同的日期表示
    plt.plot(dataList[0][0],dataList[i][1],label=name[i])
ax = plt.gca()
ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(1 if sT.createCalender().dayDiff(STARTYEAR,STARTMONTH,STARTDAY, ENDYEAR,ENDMONTH,ENDDAY)<365*3 else 5))
ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f%%"))
ax.axhline(color='black',y=0)
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
plt.legend(loc=0,ncol=len(dataList),mode="expand",borderaxespad=0.0)
plt.gcf().autofmt_xdate()
plt.grid(True)
plt.show()






