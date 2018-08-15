#coding:utf8

from sqlalchemy import create_engine
import numpy as np
import tushare as ts
import stockTools as sT
import xlrd
import xlwt

STARTYEAR = 2011   #投资起始年
STARTMONTH = 1 #投资起始月份
buyDay = 1      #投资起始日期
ENDYEAR = 2013  #投资结束年
ENDMONTH = 12  #投资结束月份
saleDay = 30  #投资结束日期
CHECKDAY = 20  #定投日期及最大回撤每月的检查点
REPORTYEARLAST = 2016 #最新年报年份

nStockInvest = 100     #购买的股数

print u"计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月---",ENDYEAR,u"年",ENDMONTH,u"月"
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('InvestResult')
ListColumnName = [u'代码',u'名称',u'投资时长（年）',u'投资收益率',u'投资年化复合收益率',u'最大回撤时的收益率',\
                  u'最大回撤出现的时间',u'投资起始时间',u'卖出股份时间',u'投资总成本',u'投资总市值',u'投资总收益',\
                  u'分红',u'平均年收益',u'总股本',u'初始股本',u'最大回撤']
for idx in range(len(ListColumnName)):
    worksheet.write(0, idx, ListColumnName[idx])

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
        print code[i], name[i]
        print "checking reports..."
        found, STARTYEAR = sT.checkStockReport(code[count], STARTYEAR, ENDYEAR-1)
        if found == False: exit(1)
        print "checking distrib..."
        if sT.checkDistrib(code[count], STARTYEAR-1, ENDYEAR-1) == False: exit(1)
        sname, yearToMarket = sT.getStockBasics(code[count])
        if yearToMarket == 0:
            print code[count], name[count], u"上市时间不详!"
            exit(1)
        print "checking DONE!"
        count += 1


engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
for i in range(count):
    foundData = False
    foundData,closePrice,buyDay=sT.getClosePrice(code[i], STARTYEAR , STARTMONTH, buyDay)
    if foundData:
        nCapitalInvest = closePrice*nStockInvest
    else:
        print "ERROR:",code[i],name[i],sT.getDateString(STARTYEAR,STARTMONTH,buyDay),"未找到该股交易信息"
        exit(1)
    ndividend = 0.0  # 总分红
    nStockTotal = 0  # 总股数
    nStockTotal = nStockInvest  # 最终获得股数，初始为购买的股数
    lostMoneyMax = 0
    lostMoneyMaxCaption = nCapitalInvest
    lostMoneyMaxTime =""
    dictColumnValues={}
    print code[i], name[i]
    for year in range(STARTYEAR,ENDYEAR+1):
        distribYear = year-1
        try:
            sqlString = "select distrib from stockreport_"
            sqlString += "%s" % (distribYear)
            sqlString += "_4 where code="
            sqlString += code[i]
            ret = conn.execute(sqlString)
        except Exception, e:
            print "ERROR: ", code[i], name[i], "connect database failure!"
            print e
            exit(1)
        resultDistrib = ret.first()
        if resultDistrib is None or resultDistrib.distrib is None:
            print "WARNING:", code[i], name[i], distribYear, u"年，数据库年报分红数据获取失败！此年可能无分红！"
            m = -1 #无分红，则分红月m的值置为-1
        else:
            try:
                sqlString = "select dividenTime from stockreport_"
                sqlString += "%s" % (distribYear)
                sqlString += "_4 where code="
                sqlString += code[i]
                ret = conn.execute(sqlString)
            except Exception, e:
                print "WARNING: ", code[i], name[i], "connect database failure!"
                print e
                exit(1)
            resultDividenDate = ret.first()
            if resultDividenDate.dividenTime is None:
                m = -1
            else:
                y, m, d = sT.splitDateString(resultDividenDate.dividenTime)
        for month in range(1, 13):
            foundData, closePrice, actualDay = sT.getClosePrice(code[i], year, month, CHECKDAY)
            if foundData==False:continue
            # 如果该月是分红月，且不是最后一年就计算此年的分红配送:最后一年年报可能未出
            # 如果价格日期大于分红登记日期表示已经除权除息，则需要计算分红送转后再计算回撤
            if (month == m and actualDay>d or month == m+1 and actualDay<=d) and year <= REPORTYEARLAST:
                #print year,month,actualDay, "计算分红" , y,m,d
                # 计算分红送转
                r, s = sT.getDistrib(resultDistrib.distrib)
                # 分红计算
                ndividend += nStockTotal * r
                # 送转增加股本计算
                nStockTotal += nStockTotal * s
                # print year, "年，每10股分红：", 10*r, "送转股数：", 10*s
            lost = nStockTotal * closePrice + ndividend - nCapitalInvest
            if lostMoneyMax > lost:#由于计算时只计算检查日时的最大回撤，可能有比检查日回撤更大的时候，尤其是最后卖出时。
                lostMoneyMax = lost
                lostMoneyMaxCaption = nCapitalInvest
                lostMoneyMaxTime = sT.getDateString(year, month, actualDay)

    if ENDMONTH==12:
        year = ENDYEAR+1
        month = 1
        saleDay = 1
    else:
        year = ENDYEAR
        month = ENDMONTH
    foundData,closePrice,saleDay=sT.getClosePrice(code[i], year, month, saleDay)
    if foundData==True:
        nCapitalTotal = nStockTotal*closePrice+ndividend
        income = nCapitalTotal-nCapitalInvest
        incomeRate = income/nCapitalInvest
        investPeriod = round(year-1-STARTYEAR+(12-STARTMONTH+1+month)/12.0,2)
        dictColumnValues[u'代码'] = code[i]
        dictColumnValues[u'名称'] = name[i]
        dictColumnValues[u'投资时长（年）'] = investPeriod
        dictColumnValues[u'投资起始时间'] = sT.getDateString(STARTYEAR,STARTMONTH,buyDay)
        dictColumnValues[u'卖出股份时间'] = sT.getDateString(year,month,saleDay)
        dictColumnValues[u'投资总成本'] = nCapitalInvest
        dictColumnValues[u'投资总市值'] = nCapitalTotal
        dictColumnValues[u'投资总收益'] = income
        dictColumnValues[u'分红'] = ndividend
        dictColumnValues[u'平均年收益'] = round(income/investPeriod,2)
        dictColumnValues[u'投资收益率'] = round(incomeRate,4)
        dictColumnValues[u'投资年化复合收益率'] = round(((incomeRate+1)**(1.0/investPeriod)-1),4)
        dictColumnValues[u'总股本'] = nStockTotal
        dictColumnValues[u'初始股本'] = nStockInvest
        dictColumnValues[u'最大回撤'] = lostMoneyMax
        dictColumnValues[u'最大回撤时的收益率'] = round(lostMoneyMax/lostMoneyMaxCaption,4)
        dictColumnValues[u'最大回撤出现的时间'] = lostMoneyMaxTime
        print u'时长：',dictColumnValues[u'投资时长（年）'],u'年,'\
              u'投资收益率:',"%.2f%%" %(dictColumnValues[u'投资收益率']*100),\
              u',最大回撤时的收益率:',"%.2f%%" %(dictColumnValues[u'最大回撤时的收益率']*100)
        for idx in range(len(ListColumnName)):
            worksheet.write(i+1, idx, dictColumnValues[ListColumnName[idx]])
    else:
        print u"获取卖出日价格失败！",year, month, saleDay

workbook.save('.\\data\\InvestResult.xls')
print "Invest result has been wrotten to InvestResult.xls"
print u"请确认已使用stockDataChecker.py进行数据检查！"






