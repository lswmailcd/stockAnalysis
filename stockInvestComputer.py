#coding:utf8

import os
from sqlalchemy import create_engine
import numpy as np
import tushare as ts
import stockTools as sT
import xlrd
import xlwt
import stockDataChecker as ck

style_percent = xlwt.easyxf(num_format_str='0.00%')

STARTYEAR = 2010 #投资起始年
STARTMONTH = 6#投资起始月份
buyDay = 1    #投资起始日期
ENDYEAR = 2014  #投资结束年
ENDMONTH = 6  #投资结束月份
saleDay = 29  #投资结束日期
checkDay = 10  #回撤检查日
REPORTYEARLAST = 2020 #最新报表年份

nStockInvest = 100     #购买的股数

print( "一次性投资计算时间段为：",STARTYEAR,u"年",STARTMONTH,u"月---",ENDYEAR,u"年",ENDMONTH,u"月")
print( "***请确保已经使用stockDataChecker.py对数据进行检查***")
str = input("不检查继续请按'回车',如需检查请按'c',退出请按'q': ")
if str=="q" : exit(0)
if str=="c" :
    dirName = os.path.dirname(os.path.realpath(__file__))
    ck.process(2008,2020,'stockList.xls')
    #os.system('python ' + dirName + '\\stockDataChecker.py 2008 2020 stockList.xls')

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
code = []
name = []
count = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="" or table.cell(i + 1, 1).value!="":
        count += 1
        code.append(table.cell(i + 1, 0).value)
        if code[i] == "":
            name.append("")
        else:
            name.append(sT.getStockNameByCode(code[i]))
            if name[i] == None:
                code[i] = ""
                continue
            sname, yearToMarket,_ ,_ = sT.getStockBasics(code[i])
            if yearToMarket == 0:
                print( code[i], name[i], u"上市时间不详!")
                exit(1)

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
for i in range(count):
    if code[i] == "" or code[i]=='0.0':
        worksheet.write(i + 1, 0, "")
        continue
    foundData = False
    foundData,closePrice,actualbuyDate=sT.getClosePriceForward(code[i], STARTYEAR , STARTMONTH, buyDay)
    if foundData:
        nCapitalInvest = closePrice*nStockInvest
    else:
        print( "ERROR:",code[i],name[i],actualbuyDate,"未找到该股交易信息")
        continue
    ndividend = 0.0  # 总分红
    nStockTotal = nStockInvest  # 最终获得股数，初始为购买的股数
    lostMoneyMax = 0
    lostMoneyMaxCaption = nCapitalInvest
    lostMoneyMaxTime =""
    dictColumnValues={}
    print( code[i], name[i])
    for year in range(STARTYEAR,ENDYEAR+1):
        distribYear = year-1
        bDividen = True
        try:
            sqlString = "select distrib from stockreport_"
            sqlString += "%s" % (distribYear)
            sqlString += "_4 where code="
            sqlString += code[i]
            ret = conn.execute(sqlString)
        except Exception as e:
            print( "ERROR: ", code[i], name[i], "connect database failure!")
            print( e)
            exit(1)
        nStockTotalBeforeDividen = nStockTotal
        resultDistrib = ret.first()
        if resultDistrib is None or resultDistrib.distrib is None:
            print( "WARNING:", code[i], name[i], distribYear, u"年分红不详，数据库年报分红数据获取失败！此年可能无分红！")
            bDividen = False #无分红
        else:
            bDividen, dividenTime = sT.getDividenTime(code[i], distribYear)
            if bDividen and ( sT.getDateString(STARTYEAR, STARTMONTH, buyDay) <= dividenTime ) \
                and ( sT.getDateString(ENDYEAR, ENDMONTH, saleDay) > dividenTime ):
                    print( dividenTime, "计算分红")
                    # 计算分红送转
                    bdis, r, s = sT.getDistrib(code[i], distribYear)
                    # 分红计算
                    ndividend += nStockTotal * r
                    # 送转增加股本计算
                    #print( "增加股本", nStockTotal * s
                    nStockTotal += nStockTotal * s
                    print( year, "年，每10股分红：", 10 * r, "送转股数：", 10 * s)
        #计算回撤
        if year==STARTYEAR:
            startMonth = STARTMONTH
        else:
            startMonth = 1
        if year==ENDYEAR:
            endMonth = ENDMONTH+1
        else:
            endMonth = 13
        for m in range(startMonth,endMonth):
            foundData, price, date = sT.getClosePriceForward( code[i], year, m, checkDay )
            if foundData:
                if bDividen and (sT.getDateString(year, m, checkDay) <= dividenTime ):
                    lost = nStockTotalBeforeDividen * price + ndividend - nCapitalInvest
                else:
                    lost = nStockTotal * price + ndividend - nCapitalInvest
                if lostMoneyMax > lost:#由于计算时只计算检查日时的最大回撤，可能有比检查日回撤更大的时候，尤其是最后卖出时。
                    lostMoneyMax = lost
                    lostMoneyMaxCaption = nCapitalInvest
                    lostMoneyMaxTime = date

    foundData,closePrice,date=sT.getClosePriceBackward(code[i], ENDYEAR, ENDMONTH, saleDay)
    #year = ENDYEAR
    if foundData==True:
        nCapitalTotal = nStockTotal*closePrice+ndividend
        income = nCapitalTotal-nCapitalInvest
        incomeRate = income/nCapitalInvest
        investPeriod = round(sT.createCalender().dayDiff(STARTYEAR,STARTMONTH,buyDay,ENDYEAR,ENDMONTH,saleDay)/365.0, 2)
        dictColumnValues[u'代码'] = code[i]
        dictColumnValues[u'名称'] = name[i]
        dictColumnValues[u'投资时长（年）'] = investPeriod
        dictColumnValues[u'投资起始时间'] = sT.getDateString(STARTYEAR,STARTMONTH,buyDay)
        dictColumnValues[u'卖出股份时间'] = date #sT.getDateString(year,saleMonth,actualsaleDay)
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
        print( u'时长：',dictColumnValues[u'投资时长（年）'],u'年,'\
              u'投资收益率:',"%.2f%%" %(dictColumnValues[u'投资收益率']*100),\
              u',最大回撤时的收益率:',"%.2f%%" %(dictColumnValues[u'最大回撤时的收益率']*100))
        for idx in range(len(ListColumnName)):
            if ListColumnName[idx].find(u'率') != -1:
                worksheet.write(i + 1, idx, dictColumnValues[ListColumnName[idx]], style_percent)
            else:
                worksheet.write(i+1, idx, dictColumnValues[ListColumnName[idx]])
    else:
        print( u"获取卖出日价格失败！",year, saleMonth, saleDay)

workbook.save('.\\data\\InvestResult.xls')
print( "Invest result has been wrotten to InvestResult.xls")
print( u"请确认已使用stockDataChecker.py进行数据检查！")






