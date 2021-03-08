# -*- coding: utf-8 -*-
import urllib2
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT
import stockGlobalSpace as sG
import bs4
import re
from random import randint

#!!!!注意，一定要保证所有日期处于日历日期内，否则程序会报错！！！
STARTYEAR = 2011 #投资起始年
STARTMONTH = 1 #投资起始月份
STARTDAY = 1      #投资起始日期
ENDYEAR = 2015  #定投结束年
ENDMONTH = 6  #定投结束月份
ENDDAY = 1  #定投结束日
BUYDAY = 20  #定投日
INTERVAL  = 1    #定投间隔的月份
INVESTMONEY = "10000"

#定投结束日即是卖出日，目前无法实现定投结束日和卖出日不同。
#SALEYEAR = 2015  #卖出年
#SALEMONTH = 6  #卖出月份
#SALEDAY = 1  #卖出日


print u"定投计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月", STARTDAY,u"日\
---",ENDYEAR,u"年",ENDMONTH,u"月", ENDDAY,u"日"

startDate = sT.getDateString(STARTYEAR, STARTMONTH, STARTDAY)
endDate = sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY)

data = xlrd.open_workbook('.\\data\\fundata.xls')
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

print u"WARNING:请注意基金历史分红情况，默认为红利再投资！"
str = raw_input("默认红利再投进行计算请按'回车',如需现金分红以进行计算请按'c',退出请按'q': ")
if str=="q" : exit(0)
stype = "1" #红利再投
if str=="c" :
    stype = "2" #现金分红

str = raw_input("如不进行分红检查请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    print("开始检查基金分红数据......")
    for i in range(count):
        if code[i] == u'': continue
        sT.checkFundDistrib(code[i])

    print("基金分红数据检查完成！")

workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('dataResult')
ListColumnName = [u'代码',u'名称',u'定投年数',u'投资收益率',u'投资年化复合收益率',u'最大回撤时的收益率',\
                  u'最大回撤出现的时间', u'最大收益', u'最大收益率', u'最大收益出现的时间', u'投资总成本',u'投资总市值',\
                  u'投资总收益',u'分红',u'平均年收益',u'总份额', u'购买份额',u'最大回撤',\
                  u'定投起始时间',u'卖出基金时间'] #u'定投结束时间'#,
for idx in range(len(ListColumnName)):
    worksheet.write(0, idx, ListColumnName[idx])

for i in range(count):
    foundData = 0
    if code[i] == u'' : continue
    url = "http://fund.eastmoney.com/data/FundInvestCaculator_AIPDatas.aspx?fcode=" + code[i]
    url = url + "&sdate=" + startDate + "&edate=" + endDate + "&shdate=" + endDate
    url = url + "&round=" + "%s" %(INTERVAL) + "&dtr=" + "%s" %(BUYDAY) + "&p=" + "0" + "&je=" + INVESTMONEY
    url = url + "&stype=" + stype + "&needfirst=" + "2" + "&jsoncallback=FundDTSY.result"
    request = urllib2.Request(url=url, headers=sG.browserHeaders)
    response = urllib2.urlopen(request)
    data = response.read()
    #data = urllib.urlopen(url).read()
    time.sleep(randint(1,3))
    infoStr = data.split('|')
    if infoStr[2]=='0期':
        print data
        continue

    dictColumnValues = {}
    investTotal = float(infoStr[3].replace(",",""))
    totalValue = float(infoStr[5].replace(",",""))
    details = infoStr[7][:-3].split("_")
    moneyTotal, shareTotal, diffWorse, diffBest, dateWorse, dateBest, worseRate, bestRate = \
    0.0, 0.0, 0.0, 0.0, "", "", 0.0,0.0
    d0 = startDate
    #获取基金分红数据，用于计算份额变动
    _, distrib = sT.getFundDistrib(code[i])
    for s in details:
        t = s.split("~")#t[0]:日期,t[1]:价格,t[2]:本金,t[3]:份额
        p = t[0].replace(",","").find("星")
        date = t[0].replace(",","")[:p]
        share = float(t[3].replace(",",""))
        for d in distrib:#d[0]:登记及除息日，d[1]:每份分红金额,d[2]:红利发放日，红利再投资日
            if d0<=d[0]<date:
                disMoney = shareTotal*d[1]
                shareTotal += disMoney/sT.getFundPrice(code[i], d[2])[1]

        d0 = date

        shareTotal += share
        moneyTotal = moneyTotal + float(t[2].replace(",",""))
        diff = float(t[1])*shareTotal - moneyTotal
        #print(float(t[1]))
        #print('diff=', diff, 'shareTotal=', shareTotal, 'date', date)
        if diff<diffWorse:
            diffWorse = diff
            dateWorse = t[0]
            worseRate = diff/moneyTotal
            #print('diffWorse=',diffWorse,'dateWorse',dateWorse)
        if diff>diffBest:
            diffBest = diff
            dateBest = t[0]
            bestRate = diff / moneyTotal
            #print('diffBest=', diffBest, 'dateBest', dateBest)

    # print(totalValue-investTotal)
    # print(shareTotal*sT.getFundPrice(code[i], endDate)[1]-moneyTotal)
    # print(totalValue==shareTotal*sT.getFundPrice(code[i], endDate)[1],investTotal==moneyTotal )
    # print shareTotal, totalValue/sT.getFundPrice(code[i], endDate)[1]
    rate = (totalValue-investTotal)/investTotal#float(infoStr[6][:-1])/100.0
    investPeriod = round(sT.createCalender().dayDiff(STARTYEAR,STARTMONTH,STARTDAY,ENDYEAR,ENDMONTH,ENDDAY)/365.0, 2)
    ratePerYear = round(((rate + 1) ** (1.0 / investPeriod) - 1), 4)
    dictColumnValues[u'代码'] = code[i]
    dictColumnValues[u'名称'] = name[i]
    dictColumnValues[u'定投年数'] = investPeriod
    dictColumnValues[u'定投起始时间'] = startDate
    #dictColumnValues[u'定投结束时间'] = endDate
    dictColumnValues[u'卖出基金时间'] = endDate
    dictColumnValues[u'投资总成本'] = moneyTotal
    dictColumnValues[u'投资总市值'] = moneyTotal*(1+rate)
    dictColumnValues[u'投资总收益'] = moneyTotal*rate
    dictColumnValues[u'分红'] = 0.0
    dictColumnValues[u'平均年收益'] = round(dictColumnValues[u'投资总收益'] / investPeriod, 2)
    dictColumnValues[u'投资收益率'] = round(rate, 4)
    dictColumnValues[u'投资年化复合收益率'] = ratePerYear
    dictColumnValues[u'总份额'] = share
    dictColumnValues[u'购买份额'] = share
    dictColumnValues[u'最大回撤'] = diffWorse
    dictColumnValues[u'最大回撤时的收益率'] = worseRate
    dictColumnValues[u'最大回撤出现的时间'] = dateWorse.decode("utf8")
    dictColumnValues[u'最大收益'] = diffBest
    dictColumnValues[u'最大收益率'] = bestRate
    dictColumnValues[u'最大收益出现的时间'] = dateBest.decode("utf8")
    for idx in range(len(ListColumnName)):
        worksheet.write(i + 1, idx, dictColumnValues[ListColumnName[idx]])

    print code[i], name[i], "收益：%.2f%%" % (rate * 100.0), "年化收益：%.2f%%" % (ratePerYear * 100.0)

workbook.save('.\\data\\dataResult.xls')
print "Invest result has been wrotten to dataResult.xls"






