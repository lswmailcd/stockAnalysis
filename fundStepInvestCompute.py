import urllib
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
import Graph as g

BONUS_SHARE = "1" #红利再投
BONUS_CASH = "2" #现金红利
style_percent = xlwt.easyxf(num_format_str='0.00%')
style_finance = xlwt.easyxf(num_format_str='￥#,##0.00')

print("\n***注意，一定要保证所有日期处于日历日期内，否则程序会报错！！！***\n")

STARTYEAR = 2021 #定投起始年
STARTMONTH = 1 #定投起始月份

ENDYEAR = 2021  #定投结束年
ENDMONTH = 11  #定投结束月份

INVESTMONEY = "5000"

#卖出日
SALEYEAR = 2021 #卖出年
SALEMONTH = 12  #卖出月份
SALEDAY = 3 #卖出日


ENDDAY = 28 #定投结束与月底，考虑2月份，则结束日定在28号
BUYDAY = 10  #定投日
INTERVAL  = 1    #定投间隔的月份


print( u"定投计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月", BUYDAY,u"日\
---",ENDYEAR,u"年",ENDMONTH,u"月", BUYDAY,u"日")

print( u"持有计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月", BUYDAY,u"日\
---",SALEYEAR,u"年",SALEMONTH,u"月", SALEDAY,u"日")

startDate = sT.getDateString(STARTYEAR, STARTMONTH, BUYDAY)
endDate = sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY)
saleDate = sT.getDateString(SALEYEAR, SALEMONTH, SALEDAY)
if endDate>saleDate: endDate=saleDate

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

print(u"WARNING:请注意基金历史分红情况，默认为红利再投资！")
str = input("默认红利再投进行计算请按'回车',如需现金分红以进行计算请按'c',退出请按'q': ")
if str=="q" : exit(0)
stype = BONUS_SHARE #红利再投
if str=="c" :
    stype = BONUS_CASH #现金分红

str = input("如不进行分红检查请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    print("开始检查基金分红和份额拆分数据......")
    for i in range(count):
        if code[i] == u'': continue
        sT.checkFundDistribSplit(code[i])
    print("基金分红和份额拆分数据检查完成！")

#for i in range(count):
#    sT.checkFundPrice(code[i], startDate, saleDate)

workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('dataResult')
ListColumnName = [u'代码',u'名称',u'定投年数',u'持有年数',u'投资收益率',u'投资年化复合收益率',\
                  u'最佳收益率',u'最佳收益额',u'最佳收益时间',\
                  u'最差收益率',u'最差收益额',u'最差收益时间',\
                  u'最大回撤额时的收益率',u'最大回撤额', u'最大回撤额出现的时间', \
                  u'最大收益额时的收益率',u'最大收益额', u'最大收益额出现的时间', \
                  u'投资总成本',u'投资总市值',u'投资总收益',u'平均年收益',u'分红',u'总份额', u'购买份额',\
                  u'定投起始时间',u'定投结束时间',u'卖出基金时间',"投资日"]
for idx in range(len(ListColumnName)):
    worksheet.write(0, idx, ListColumnName[idx])

lsInfo=[]
dataList=[]
for i in range(count):
    foundData = 0
    if code[i] == u'' : continue
    url = "http://fund.eastmoney.com/data/FundInvestCaculator_AIPDatas.aspx?fcode=" + code[i]
    url = url + "&sdate=" + startDate + "&edate=" + endDate + "&shdate=" + saleDate
    url = url + "&round=" + "%s" %(INTERVAL) + "&dtr=" + "%s" %(BUYDAY) + "&p=" + "0" + "&je=" + INVESTMONEY
    url = url + "&stype=" + stype + "&needfirst=" + "2" + "&jsoncallback=FundDTSY.result"
    response = urllib.request.urlopen(url=url)
    #response = urllib.urlopen(request)
    data = response.read().decode('utf-8')
    #data = urllib.urlopen(url).read()
    time.sleep(randint(1,3))
    infoStr = data.split('|')
    if infoStr==['']:
        print(data)
        continue

    name[i] = infoStr[1]

    dictColumnValues = {}
    investTotal = float(infoStr[3].replace(",",""))
    details = infoStr[7][:-3].split("_")
    firstInvest = details[0]
    t = firstInvest.split("~")  # t[0]:日期,t[1]:价格,t[2]:本金,t[3]:份额
    p = t[0].replace(",", "").find("星")
    actualStartDate = t[0].replace(",", "")[:p]

    rateList, dateList = [], []
    moneyTotal, shareTotalInvest, shareTotal, diffWorst, diffBest, dateWorst, dateBest, diffWorstRate, diffBestRate, \
    rateWorst, rateBest, dateRateWorst, dateRateBest, bonusTotal, lostWorst, earnBest = \
    0.0, 0.0, 0.0, 0.0, 0.0, "", "", 0.0,0.0, 0.0,0.0,"", "", 0.0, 0.0, 0.0
    d0 = actualStartDate
    #获取基金分红数据，用于计算份额变动（红利再投）或分红情况（现金红利）
    _, distrib = sT.getFundDistrib(code[i])
    # 获取基金拆分数据，用于计算份额变动
    _, shareSplit = sT.getFundShareSplit(code[i])
    shareSplit=[s for s in shareSplit if s[0]>actualStartDate]
    for s in details:
        t = s.split("~")#t[0]:日期,t[1]:价格,t[2]:本金,t[3]:份额
        p = t[0].replace(",","").find("星")
        date = t[0].replace(",","")[:p]
        dateList.append(date)
        #print(date)
        if shareSplit!=[] and shareSplit[0][0]<=date:#拥有的份额按比例拆分
            shareTotalInvest *= shareSplit[0][1]
            shareTotal *= shareSplit[0][1]
            del shareSplit[0]
        share = float(t[3].replace(",",""))
        shareTotalInvest += share
        shareTotal += share
        for d in distrib:#d[0]:登记及除息日，d[1]:每份分红金额,d[2]:红利发放日，红利再投资日
            if d0<=d[0]<date:
                disMoney = shareTotal*d[1]
                if stype == BONUS_SHARE:#红利再投
                    shareTotal += disMoney/sT.getFundPrice(code[i], d[2])[1]
                else:#现金红利
                    bonusTotal += disMoney

        d0 = date

        moneyTotal = moneyTotal + float(t[2].replace(",",""))
        diff = float(t[1])*shareTotal - moneyTotal
        rate = diff/moneyTotal
        rateList.append(rate)
        #print(float(t[1]))
        #print('diff=', diff, 'shareTotal=', shareTotal, 'date', date)
        if diff<diffWorst:
            diffWorst = diff
            dateWorst = t[0]
            diffWorstRate = rate
            #print('diffWorse=',diffWorse,'dateWorse',dateWorse)
        if diff>diffBest:
            diffBest = diff
            dateBest = t[0]
            diffBestRate = rate
            #print('diffBest=', diffBest, 'dateBest', dateBest)
        if rateWorst>rate:
            rateWorst = rate
            dateRateWorst = t[0]
            lostWorst = diff
        if rateBest<rate:
            rateBest = rate
            dateRateBest = t[0]
            earnBest = diff

    # print(totalValue-investTotal)
    # print(shareTotal*sT.getFundPrice(code[i], endDate)[1]-moneyTotal)
    # print(totalValue==shareTotal*sT.getFundPrice(code[i], endDate)[1],investTotal==moneyTotal )
    # print shareTotal, totalValue/sT.getFundPrice(code[i], endDate)[1]

    y0,m0,d0 = sT.splitDateString(endDate)
    y1, m1, d1 = sT.splitDateString(saleDate)
    if sT.createCalender().dayDiff( y0,m0,d0, y1, m1, d1 )>30:
        # 计算定投结束日至卖出日之间每月的市值
        if code[i] == u'' : continue
        url = "http://fund.eastmoney.com/data/FundInvestCaculator_AIPDatas.aspx?fcode=" + code[i]
        url = url + "&sdate=" + endDate + "&edate=" + saleDate + "&shdate=" + saleDate
        url = url + "&round=" + "%s" %(INTERVAL) + "&dtr=" + "%s" %(BUYDAY) + "&p=" + "0" + "&je=" + INVESTMONEY
        url = url + "&stype=" + stype + "&needfirst=" + "2" + "&jsoncallback=FundDTSY.result"
        response = urllib.request.urlopen(url=url)
        #response = urllib.urlopen(request)
        data = response.read().decode('utf-8')
        #data = urllib.urlopen(url).read()
        time.sleep(randint(1,3))
        infoStr = data.split('|')
        if infoStr==['']:
            print(data)
            continue

        name[i] = infoStr[1]

        dictColumnValues = {}
        investTotal = float(infoStr[3].replace(",",""))
        details = infoStr[7][:-3].split("_")
        firstInvest = details[0]
        t = firstInvest.split("~")  # t[0]:日期,t[1]:价格,t[2]:本金,t[3]:份额
        p = t[0].replace(",", "").find("星")
        ownStartDate = t[0].replace(",", "")[:p]

        # moneyTotal, shareTotalInvest, shareTotal, diffWorst, diffBest, dateWorst, dateBest, diffWorstRate, diffBestRate, \
        # rateWorst, rateBest, dateRateWorst, dateRateBest, bonusTotal, lostWorst, earnBest = \
        # 0.0, 0.0, 0.0, 0.0, 0.0, "", "", 0.0,0.0, 0.0,0.0,"", "", 0.0, 0.0, 0.0
        d0 = ownStartDate
        #获取基金分红数据，用于计算份额变动（红利再投）或分红情况（现金红利）
        _, distrib = sT.getFundDistrib(code[i])
        # 获取基金拆分数据，用于计算份额变动
        _, shareSplit = sT.getFundShareSplit(code[i])
        shareSplit=[s for s in shareSplit if s[0]>ownStartDate]
        for s in details:
            t = s.split("~")#t[0]:日期,t[1]:价格,t[2]:本金,t[3]:份额
            p = t[0].replace(",","").find("星")
            date = t[0].replace(",","")[:p]
            dateList.append(date)
             #print(date)
            if shareSplit!=[] and shareSplit[0][0]<=date:#拥有的份额按比例拆分
                shareTotalInvest *= shareSplit[0][1]
                shareTotal *= shareSplit[0][1]
                del shareSplit[0]
            for d in distrib:#d[0]:登记及除息日，d[1]:每份分红金额,d[2]:红利发放日，红利再投资日
                if d0<=d[0]<date:
                    disMoney = shareTotal*d[1]
                    if stype == BONUS_SHARE:#红利再投
                        shareTotal += disMoney/sT.getFundPrice(code[i], d[2])[1]
                    else:#现金红利
                        bonusTotal += disMoney

            d0 = date

            #moneyTotal = moneyTotal + float(t[2].replace(",",""))
            diff = float(t[1])*shareTotal - moneyTotal
            rate = diff/moneyTotal
            rateList.append(rate)
            if diff<diffWorst:
                diffWorst = diff
                dateWorst = t[0]
                diffWorstRate = rate
                #print('diffWorse=',diffWorse,'dateWorse',dateWorse)
            if diff>diffBest:
                diffBest = diff
                dateBest = t[0]
                diffBestRate = rate
                #print('diffBest=', diffBest, 'dateBest', dateBest)
            if rateWorst>rate:
                rateWorst = rate
                dateRateWorst = t[0]
                lostWorst = diff
            if rateBest<rate:
                rateBest = rate
                dateRateBest = t[0]
                earnBest = diff
    else:
        #计算定投结束日至卖出日之间的拆分和红利
        dateSet = set()
        for s in shareSplit:
            dateSet.add(s[0])
        for d in distrib:
            dateSet.add(d[0])
        lsDate = [ d for d in dateSet]
        lsDate.sort()
        for d in lsDate:
            if endDate<=d<=saleDate:
                for s in shareSplit:
                    if d == s[0]:
                        shareTotalInvest *= s[1]
                        shareTotal *= s[1]
                        break
                for db in distrib:
                    if d == db[0]:
                        disMoney = shareTotal * db[1]
                        if stype == BONUS_SHARE:  # 红利再投
                            shareTotal += disMoney / sT.getFundPrice(code[i], db[2])[1]
                        else:  # 现金红利
                            bonusTotal += disMoney
                        break

    #计算卖出日总市值
    found, price = sT.getFundPrice(code[i], saleDate)
    if not found:
        print("无法获得 {} {}的基金净值".format(name[i], saleDate))
        exit(1)
    totalValue = shareTotal*sT.getFundPrice(code[i], saleDate)[1]
    rate = (totalValue-moneyTotal)/moneyTotal
    dateList.append(saleDate)
    rateList.append(rate)
    dataList.append([dateList, rateList])
    #定投时长
    y,m,d=sT.splitDateString(actualStartDate)
    investPeriod = round(sT.createCalender().dayDiff(y,m,d,ENDYEAR,ENDMONTH,BUYDAY)/365.0, 2)
    # 持有时长
    earnPeriod = round(sT.createCalender().dayDiff(y,m,d,SALEYEAR,SALEMONTH,SALEDAY)/365.0, 2)
    ratePerYear = round(((rate + 1) ** (1.0 / earnPeriod) - 1), 4)
    dictColumnValues[u'代码'] = code[i]
    dictColumnValues[u'名称'] = name[i]
    dictColumnValues[u'定投年数'] = investPeriod
    dictColumnValues[u'定投起始时间'] = actualStartDate
    dictColumnValues[u'定投结束时间'] = endDate
    dictColumnValues[u'持有年数'] = earnPeriod
    dictColumnValues[u'卖出基金时间'] = saleDate
    dictColumnValues[u'投资总成本'] = moneyTotal
    dictColumnValues[u'投资总市值'] = moneyTotal*(1+rate)
    dictColumnValues[u'投资总收益'] = moneyTotal*rate
    dictColumnValues[u'分红'] = bonusTotal
    dictColumnValues[u'平均年收益'] = round(dictColumnValues[u'投资总收益'] / earnPeriod, 2)
    dictColumnValues[u'投资收益率'] = round(rate, 4)
    dictColumnValues[u'投资年化复合收益率'] = ratePerYear
    dictColumnValues[u'总份额'] = shareTotal
    dictColumnValues[u'购买份额'] = shareTotalInvest
    dictColumnValues[u'最大回撤额'] = diffWorst
    dictColumnValues[u'最大回撤额时的收益率'] = diffWorstRate
    dictColumnValues[u'最大回撤额出现的时间'] = dateWorst
    dictColumnValues[u'最大收益额'] = diffBest
    dictColumnValues[u'最大收益额时的收益率'] = diffBestRate
    dictColumnValues[u'最大收益额出现的时间'] = dateBest
    dictColumnValues[u'最佳收益率'] = rateBest
    dictColumnValues[u'最佳收益额'] = earnBest
    dictColumnValues[u'最佳收益时间'] = dateRateBest
    dictColumnValues[u'最差收益率'] = rateWorst
    dictColumnValues[u'最差收益额'] = lostWorst
    dictColumnValues[u'最差收益时间'] = dateRateWorst
    dictColumnValues[u'投资日'] = BUYDAY

    lsInfo.append( (dictColumnValues[u'投资收益率'], dictColumnValues) )


lsInfo.sort( reverse=True )
for i, Info in enumerate(lsInfo):
    for idx in range(len(ListColumnName)):
        if ListColumnName[idx].find(u'率') != -1:
            worksheet.write(i + 1, idx, Info[1][ListColumnName[idx]], style_percent)
        elif ListColumnName[idx].find(u'投资总成本') != -1 or ListColumnName[idx].find(u'投资总市值') != -1 \
                or ListColumnName[idx].find(u'投资总收益') != -1 or ListColumnName[idx].find(u'平均年收益') != -1 \
                or ListColumnName[idx].find(u'分红') != -1 or ListColumnName[idx].find(u'最佳收益额') != -1 \
                or ListColumnName[idx].find(u'最差收益额') != -1 or ListColumnName[idx].find(u'最大回撤额') != -1 \
                or ListColumnName[idx].find(u'最大收益额') != -1:
            worksheet.write(i + 1, idx, Info[1][ListColumnName[idx]], style_finance)
        else:
            worksheet.write(i + 1, idx, Info[1][ListColumnName[idx]])

    rate = Info[0]; ratePerYear=Info[1][u'投资年化复合收益率']
    print( code[i], name[i], "总收益率：%.2f%%" % (rate * 100.0), "年化收益率：%.2f%%" % (ratePerYear * 100.0))

try:
    workbook.save('.\\data\\dataResult.xls')
except Exception as e:
    print(e)
    str = input("文件检查无误请按'ok'！")
    while str!='ok': str = input("文件检查无误请输入'ok'！")
    workbook.save('.\\data\\dataResult.xls')
print( "Invest result has been wrotten to dataResult.xls")

title="{}至{}基金定投收益图,卖出时间{}".format(startDate, endDate,saleDate)
yScale = 5
xList = dataList[0][0]
yList = [d[1] for d in dataList]
dir = ".\\data\\"+title+".png"
g.drawRateChat(xList, yList, name, title)









