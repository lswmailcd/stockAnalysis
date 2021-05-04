#coding:utf8

import os
from sqlalchemy import create_engine
import numpy as np
import stockTools as sT
import xlrd
import xlwt
import time
import stockDataChecker as ck

STARTYEAR = 2020 #定投起始年
STARTMONTH = 12  #定投起始月份
ENDYEAR = 2021  #定投结束年
ENDMONTH = 4 #定投结束月份
ENDDAY = 30 #定投卖出日
BUYDAY=(10,) #每月中的定投日期列表
REPORTYEARLAST = 2020 #最新报表年份

moneyLimit = 10000  #每次定投金额上限，实际金额根据买的股数取整

style_percent = xlwt.easyxf(num_format_str='0.00%')

print( u"定投计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月---",ENDYEAR,u"年",ENDMONTH,u"月")
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
                  u'投资起始时间',u'卖出股份时间',u"每月最小投资额",u"每月最大投资额","投资日"]
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
                           sT.getDateString(ENDYEAR, ENDMONTH, ENDDAY))
        if s == "c":
            ck.subprocess(code[count], 2008, REPORTYEARLAST)
        count += 1


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
    for year in range(STARTYEAR,ENDYEAR+1):
        # 检查本年分红送配情况
        distribYear = year-1
        try:
            sqlString = "select distrib from stockreport_"
            sqlString += "%s" % (distribYear)
            sqlString += "_4 where code="
            sqlString += code[i]
            ret = conn.execute(sqlString)
            resultDistrib = ret.first()
            if resultDistrib is None or resultDistrib.distrib is None:
                print( "WARNING:", code[i], name[i], distribYear, u"年，数据库年报分红数据获取失败！此年可能无分红！")
                m = -1  # 无分红，则分红月m的值置为-1
            else:
                try:
                    sqlString = "select dividenTime from stockreport_sup_"
                    sqlString += "%s" % (distribYear)
                    sqlString += "_4 where code="
                    sqlString += code[i]
                    ret = conn.execute(sqlString)
                    resultDividenDate = ret.first()
                    if resultDividenDate.dividenTime is None:
                        m = -1
                    else:
                        y, m, d = sT.splitDateString(resultDividenDate.dividenTime)
                except Exception as e:
                    print( "ERROR: ", code[i], name[i], "connect database failure!")
                    print( e)
                    exit(1)
        except Exception as e:
            print( "WARNING: ", code[i], name[i], distribYear,"年stockreport数据表不存在！")
            m=-1

        #逐月定投计算
        nStockThisYear = 0
        nCapitalThisYear = 0.0
        if year==ENDYEAR:
            endMonth = ENDMONTH+1
        else:
            endMonth = 13
        if year==STARTYEAR:
            startMonth = STARTMONTH
        else:
            startMonth = 1
        #step = 1
        #if year==STARTYEAR: step=1
        bDistrib = False
        for month in range(startMonth,endMonth,1):
            for tradeDay in BUYDAY:
                foundData,closePrice, actualDate=sT.getClosePriceBackward(code[i], year, month, tradeDay)
                actY, actM, actD = sT.splitDateString(actualDate)
                if foundData==False:
                    print( "WARNING:",year, month, u"获取连网股价失败！可能此月股票停牌，暂停定投！")
                    continue
                # 如果该月是分红月，且不是最后一年就计算此年的分红配送（最后一年年报可能未出）
                # 如果价格日期大于分红登记日期表示已经除权除息，则需要计算分红送转后再计算回撤
                if (month == m and actD>d or month == m+1 and bDistrib==False) and year <= REPORTYEARLAST:
                    bDistrib = True
                    #print( year,month,actualDay, "计算分红" , y,m,d
                    # 计算分红送转
                    r, s = sT.parseDistrib(resultDistrib.distrib)
                    # 分红计算
                    ndividend += nStockTotal * r
                    # 送转增加股本计算
                    nStockTotal += nStockTotal * s
                    # print( year, "年，每10股分红：", 10*r, "送转股数：", 10*s
                nStockThisMonth = int(moneyLimit/closePrice/100)*100 #买入股数，如结果为560股则买入500股
                nStockInvest += nStockThisMonth #总计购入股本
                if nStockThisMonth==0: nStockThisMonth = 100 #至少保证买入100股
                nCapitalInvestThisMonth = nStockThisMonth*closePrice+5  #5元为买入手续费
                if nMaxInvPerMonth<nCapitalInvestThisMonth: nMaxInvPerMonth = nCapitalInvestThisMonth
                if nMinInvPerMonth>nCapitalInvestThisMonth: nMinInvPerMonth = nCapitalInvestThisMonth
                #print( year,month,actualDay,closePrice,nStockTotal,nCapitalInvest
                nStockTotal += nStockThisMonth    #本年总计股数
                nCapitalInvest += nCapitalInvestThisMonth  #本月投入成本
                profit = nStockTotal*closePrice+ndividend-nCapitalInvest
                rate = profit/nCapitalInvest
                tradeDate = sT.getDateString(year, month, actD)
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

    if ENDMONTH==12:
        year = ENDYEAR+1
        month = 1
    else:
        year = ENDYEAR
        month = ENDMONTH+1
    foundData,closePrice, actualDate=sT.getClosePriceBackward(code[i],ENDYEAR, ENDMONTH, ENDDAY)
    actY, actM, actD = sT.splitDateString(actualDate)
    if foundData==True:
        nCapitalTotal = nStockTotal*closePrice+ndividend
        income = nCapitalTotal-nCapitalInvest
        incomeRate = income/nCapitalInvest
        investPeriod = round(sT.createCalender().dayDiff(STARTYEAR,STARTMONTH,1,year,actM, actD)/365.0, 2)
        dictColumnValues[u'代码'] = code[i]
        dictColumnValues[u'名称'] = name[i]
        dictColumnValues[u'投资年数'] = investPeriod
        dictColumnValues[u'投资起始时间'] = sT.getDateString(STARTYEAR,STARTMONTH,1)
        dictColumnValues[u'卖出股份时间'] = sT.getDateString(ENDYEAR,ENDMONTH,ENDDAY)
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
        print( u'时长：',dictColumnValues[u'投资年数'],u'年 ',\
              u'投资收益率:',"%.2f%%" %(dictColumnValues[u'投资收益率']*100), \
              u'投资年化复合收益率:', "%.2f%%" % (dictColumnValues[u'投资年化复合收益率'] * 100))
        for idx in range(len(ListColumnName)):
            if ListColumnName[idx].find(u'率') != -1:
                worksheet.write(i + 1, idx, dictColumnValues[ListColumnName[idx]], style_percent)
            else:
                worksheet.write(i + 1, idx, dictColumnValues[ListColumnName[idx]])
    else:
        print( u"获取卖出日价格失败！",actY, actM, actD)
workbook.save('.\\data\\StepInvestResult.xls')
print( "Invest result has been wrotten to StepInvestResult.xls")
print( u"请确认已使用stockDataChecker.py进行数据检查！")











