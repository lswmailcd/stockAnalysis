#coding:utf8

import os
from sqlalchemy import create_engine
import numpy as np
import stockTools as sT
import xlrd
import xlwt
import time
import stockDataChecker as ck
import Graph as g

bSorting = False #是否按收益率降序排列

STARTYEAR = 2020 #定投起始年
STARTMONTH = 12 #定投起始月份

ENDYEAR = 2022  #定投结束年
ENDMONTH = 1  #定投结束月份

#卖出日
SALEYEAR = 2022 #卖出年
SALEMONTH = 1  #卖出月份
SALEDAY = 10 #卖出日

BUYDAY=(10,) #每月中的定投日期列表
REPORTYEARLAST = 2020 #最新报表年份

moneyLimit = 10000  #每次定投金额上限，实际金额根据买的股数取整

style_percent = xlwt.easyxf(num_format_str='0.00%')
style_finance = xlwt.easyxf(num_format_str='￥#,##0.00')

print( u"定投计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月---",ENDYEAR,u"年",ENDMONTH,u"月")
print("定投日期列表：",BUYDAY)

print( u"***请确保已经使用stockDataChecker.py对数据进行检查***")
s = input("不检查继续请按'回车',如需检查请按'c',退出请按'q': ")
if s=="q" : exit(0)

workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('StepInvestResult')
ListColumnName = [u'代码',u'名称',u'投资年数',u'投资收益率',u'投资年化复合收益率',\
                  u'最佳收益率',u'最佳收益额',u'最佳收益时间',\
                  u'最差收益率',u'最差收益额',u'最差收益时间',\
                  u'最大回撤额时的收益率',u'最大回撤额', u'最大回撤额出现的时间', \
                  u'最大收益额时的收益率',u'最大收益额', u'最大收益额出现的时间', \
                  u'投资总成本',u'投资总市值',u'投资总收益',u'平均年收益',u'分红',u'总股本',u'购买股本',\
                  u'定投起始时间',u'定投结束时间',u'卖出股份时间',u"每月最小投资额",u"每月最大投资额","投资日"]
for idx in range(len(ListColumnName)):
    worksheet.write(0, idx, ListColumnName[idx])

data = xlrd.open_workbook('.\\data\\StockList.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.compat.unicode)
name = np.array(a, dtype=np.compat.unicode)
count  = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[count] = table.cell(i + 1, 0).value
        name[count] = sT.getStockNameByCode(code[count])
        sname, yearToMarket,_,_ = sT.getStockBasics(code[count])
        if yearToMarket == 0:
            print( code[count], name[count], u"上市时间不详!")
            exit(1)
        sT.checkStockPrice(code[count], sT.getDateString(STARTYEAR, STARTMONTH, 1), \
                           sT.getDateString(SALEYEAR, SALEMONTH, SALEDAY))
        if s == "c":
            ck.subprocess(code[count], 2008, REPORTYEARLAST)
        count += 1

dataList=[]
lsStockInfo=[]
engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
for i in range(count):
    nCapitalInvest = 0.0  # 总投入
    ndividend = 0.0  # 总分红
    nStockTotal = 0  # 总股数
    nStockInvest = 0  # 购买的股数
    lostMoneyMax = sT.sG.sINF  # 最大回撤的损失
    lostMoneyMaxCaption = 0  #最大回撤时投入的总资本
    earnMoneyMax = sT.sG.sNINF  # 最大收益的利润
    earnMoneyMaxCaption = 0  #最大收益时投入的总资本
    dictColumnValues = {}
    lostMoneyMaxTime = ""
    earnMoneyMaxTime = ""
    nMaxInvPerMonth = 0.0
    nMinInvPerMonth = 10000.0
    worstRate = 0.0
    bestRate = 0.0
    worstLost = 0.0
    bestEarn = 0.0
    worstRateTime = ""
    bestRateTime = ""
    print( code[i],name[i])
    bFirstInvest = True
    rateList, dateList = [], []
    for year in range(STARTYEAR,ENDYEAR+1):
        #逐月定投计算
        nStockThisYear = 0
        nCapitalThisYear = 0.0
        startMonth = STARTMONTH if year == STARTYEAR else 1
        endMonth = ENDMONTH+1 if year==ENDYEAR else 13
        bDistrib = False
        for month in range(startMonth,endMonth,1):
            for tradeDay in BUYDAY:
                foundData, closePrice, tDate = sT.getClosePriceBackward(code[i], year, month, tradeDay)
                actY, actM, actD = sT.splitDateString(tDate)
                if foundData==False or not(actM==month and actY==year):#如果当月没有开市
                    print( "WARNING:",year, month, u"获取连网股价失败！可能此月股票停牌，暂停定投！")
                    rateList.append( 0.0 if rateList==[] else rateList[-1] )
                    dateList.append(sT.getDateString( year, month, tradeDay))
                    continue
                if bFirstInvest:
                    firstInvestYear = actY; firstInvestMonth = actM; firstInvestDay = actD
                    bFirstInvest = False
                # 如果该月是分红月，且不是最后一年就计算此年的分红配送（最后一年年报可能未出）
                # 如果价格日期大于分红登记日期表示已经除权除息，则需要计算分红送转后再计算回撤
                _, dividenDate = sT.getDividenTime(code[i], year-1)
                y, m, d = sT.splitDateString(dividenDate)
                if (month == m and actD>=d or month == m+1 and bDistrib==False) and year <= REPORTYEARLAST+1:
                    bDistrib = True
                    #print( year,month,actualDay, "计算分红" , y,m,d
                    # 计算分红送转
                    _, r, s = sT.getDistrib(code[i], year-1)
                    # 分红计算
                    ndividend += nStockTotal * r
                    # 送转增加股本计算
                    nStockTotal += nStockTotal * s
                    #print( year, "年，每10股分红：", 10*r, "送转股数：", 10*s )

                # 当月买入股数，如结果为560股则买入500股
                nStockThisMonth = int(moneyLimit/closePrice/100)*100
                if nStockThisMonth==0:
                    nStockThisMonth = 100 #至少保证买入100股
                nStockInvest += nStockThisMonth  # 总计购入股本
                nCapitalInvestThisMonth = nStockThisMonth*closePrice+5  #5元为买入手续费
                if nMaxInvPerMonth<nCapitalInvestThisMonth: nMaxInvPerMonth = nCapitalInvestThisMonth
                if nMinInvPerMonth>nCapitalInvestThisMonth: nMinInvPerMonth = nCapitalInvestThisMonth
                #print( year,month,actualDay,closePrice,nStockTotal,nCapitalInvest
                nStockTotal += nStockThisMonth    #本年总计股数
                nCapitalInvest += nCapitalInvestThisMonth  #本月投入成本
                profit = nStockTotal*closePrice+ndividend-nCapitalInvest
                rate = profit/nCapitalInvest
                rateList.append(rate)
                tradeDate = sT.getDateString(year, month, actD)
                dateList.append(tradeDate)
                if lostMoneyMax>profit:#由于计算时只计算检查日时的最大回撤，可能有比检查日回撤更大的时候，尤其是最后卖出时。
                    lostMoneyMax = profit
                    lostMoneyMaxCaption = nCapitalInvest
                    lostMoneyMaxTime = tradeDate
                if earnMoneyMax<profit:#由于计算时只计算检查日时的最大收益，可能有比检查日收益更大的时候，尤其是最后卖出时。
                    earnMoneyMax = profit
                    earnMoneyMaxCaption = nCapitalInvest
                    earnMoneyMaxTime = tradeDate
                if rate<worstRate:
                    worstRate = rate
                    worstRateTime = tradeDate
                    worstLost = profit
                if rate>bestRate:
                    bestRate = rate
                    bestRateTime = tradeDate
                    bestEarn = profit

    foundData,closePrice, actualDate=sT.getClosePriceBackward(code[i], SALEYEAR, SALEMONTH, SALEDAY)
    actY, actM, actD = sT.splitDateString(actualDate)
    if foundData==True:
        if dateList[-1]<actualDate:
            lsDistrib=[]
            for year in range(ENDYEAR-1, actY):
                found1, m, s = sT.getDistrib(code[i], year)
                found2, time = sT.getDividenTime(code[i], year)
                if found1 and found2: lsDistrib.append((m,s,time))
            for db in lsDistrib:
                if dateList[-1]<=db[2]<actualDate:
                    # 分红计算
                    ndividend += nStockTotal * db[0]
                    # 送转增加股本计算
                    nStockTotal += nStockTotal * db[1]
        nCapitalTotal = nStockTotal*closePrice+ndividend
        income = nCapitalTotal-nCapitalInvest
        incomeRate = income/nCapitalInvest
        investPeriod = round(sT.createCalender().dayDiff(firstInvestYear,firstInvestMonth,firstInvestDay,actY,actM, actD)/365.0, 2)
        dictColumnValues[u'代码'] = code[i]
        dictColumnValues[u'名称'] = name[i]
        dictColumnValues[u'投资年数'] = investPeriod
        dictColumnValues[u'定投起始时间'] = sT.getDateString(firstInvestYear,firstInvestMonth,firstInvestDay)
        dictColumnValues[u'定投结束时间'] = sT.getDateString(ENDYEAR, ENDMONTH, BUYDAY[-1])
        dictColumnValues[u'卖出股份时间'] = sT.getDateString(actY,actM,actD)
        dictColumnValues[u'投资总成本'] = nCapitalInvest
        dictColumnValues[u'投资总市值'] = nCapitalTotal
        dictColumnValues[u'投资总收益'] = income
        dictColumnValues[u'分红'] = ndividend
        dictColumnValues[u'平均年收益'] = round(income/investPeriod,2)
        dictColumnValues[u'投资收益率'] = round(incomeRate,4)
        dictColumnValues[u'投资年化复合收益率'] = round(((incomeRate+1)**(1.0/investPeriod)-1),4)
        dictColumnValues[u'总股本'] = nStockTotal
        dictColumnValues[u'购买股本'] = nStockInvest
        dictColumnValues[u"每月最小投资额"] = nMinInvPerMonth
        dictColumnValues[u"每月最大投资额"] = nMaxInvPerMonth
        dictColumnValues[u'最大回撤额'] = lostMoneyMax
        dictColumnValues[u'最大回撤额时的收益率'] = round(lostMoneyMax/lostMoneyMaxCaption,4)
        dictColumnValues[u'最大回撤额出现的时间'] = lostMoneyMaxTime
        dictColumnValues[u'最大收益额'] = earnMoneyMax
        dictColumnValues[u'最大收益额时的收益率'] = round(earnMoneyMax/earnMoneyMaxCaption,4)
        dictColumnValues[u'最大收益额出现的时间'] = earnMoneyMaxTime
        dictColumnValues[u'最佳收益率'] = bestRate
        dictColumnValues[u'最差收益率'] = worstRate
        dictColumnValues[u'最佳收益额'] = bestEarn
        dictColumnValues[u'最差收益额'] = worstLost
        dictColumnValues[u'最佳收益时间'] = bestRateTime
        dictColumnValues[u'最差收益时间'] = worstRateTime
        s = "-".join([str(x) for x in BUYDAY])
        dictColumnValues[u'投资日'] = s
        lsStockInfo.append((dictColumnValues[u'投资收益率'], dictColumnValues))
        rateList.append(dictColumnValues[u'投资收益率'])
        dateList.append(actualDate)
        dataList.append([dateList,rateList])
        print( u'时长：',dictColumnValues[u'投资年数'],u'年 ',\
              u'投资收益率:',"%.2f%%" %(dictColumnValues[u'投资收益率']*100), \
              u'投资年化复合收益率:', "%.2f%%" % (dictColumnValues[u'投资年化复合收益率'] * 100))
    else:
        print( u"获取卖出日价格失败！",actY, actM, actD)

if bSorting: lsStockInfo.sort( reverse=True )
for i, stockInfo in enumerate(lsStockInfo):
    for idx in range(len(ListColumnName)):
        if ListColumnName[idx].find(u'率') != -1:
            worksheet.write(i + 1, idx, stockInfo[1][ListColumnName[idx]], style_percent)
        elif ListColumnName[idx].find(u'投资总成本')!=-1 or ListColumnName[idx].find(u'投资总市值')!=-1 \
             or ListColumnName[idx].find(u'投资总收益')!=-1 or ListColumnName[idx].find(u'平均年收益')!=-1 \
             or ListColumnName[idx].find(u'分红')!=-1 or ListColumnName[idx].find(u'最佳收益额')!=-1 \
             or ListColumnName[idx].find(u'最差收益额') != -1 or ListColumnName[idx].find(u'最大回撤额') != -1 \
             or ListColumnName[idx].find(u'最大收益额') != -1:
            worksheet.write(i + 1, idx, stockInfo[1][ListColumnName[idx]], style_finance)
        else:
            worksheet.write(i + 1, idx, stockInfo[1][ListColumnName[idx]])

try:
    workbook.save('.\\data\\StepInvestResult.xls')
except Exception as e:
    print(e)
    str = input("文件检查无误请输入'ok'！")
    while str!='ok': str = input("文件检查无误请输入'ok'！")
    workbook.save('.\\data\\StepInvestResult.xls')
print( "Invest result has been wrotten to StepInvestResult.xls")
print( u"请确认已使用stockDataChecker.py进行数据检查！")

title="{}至{}股票定投收益图,卖出日{}".format(sT.getDateString(STARTYEAR,STARTMONTH,BUYDAY[0]), sT.getDateString(ENDYEAR,ENDMONTH,BUYDAY[-1]), actualDate)
yScale = 10
xList = dataList[0][0]
yList = [d[1] for d in dataList]
g.drawRateChat(xList, yList, name, title )














