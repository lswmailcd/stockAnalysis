#coding:utf-8

from sqlalchemy import create_engine
import numpy as np
import urllib
import bs4
import time
import xlrd
import xlwt
import stockTools as sT

STARTYEAR = 2008
ENDYEAR = 2017

print "*******************stockDataChecker开始检查......*******************"
data = xlrd.open_workbook('.\\data\\StockList.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
stockType = np.array(a, dtype=np.unicode)
found = np.zeros([nrows])
count  = 0

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[count] = table.cell(i + 1, 0).value
        name[count] = sT.getStockNameByCode(code[count]).decode('utf8')
        stockType[count] = sT.getStockType(code[count])
        count += 1

print "开始检查年报数据情况..."
for i in range(count):
    sqlString = "select timetomarket from stockbasics_20180428 "
    sqlString += "where code="
    sqlString += code[i]
    bAccessDataFinished = False
    ret = conn.execute(sqlString)
    result = ret.first()
    if result is None:
        print  code[i], name[i] ,"股票基本数据获取失败！"
        continue
    elif result.timetomarket == 0:
        print  code[i], name[i],"股票上市时间数据为空！"
        continue
    yearToMarket = int(result.timetomarket / 1E4)
    print code[i], name[i], yearToMarket,"年上市！"
    if yearToMarket>STARTYEAR:
        print code[i], name[i],"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!"
        STARTYEAR = yearToMarket
    bNeedWebData = False
    bAccessWebData = False
    for year in range(STARTYEAR, ENDYEAR + 1):
        sqlString = "select code from stockreport_"
        sqlString += "%s" %(year)
        sqlString += "_4 "
        sqlString += "where code="
        sqlString += code[i]
        ret = conn.execute(sqlString)
        result = ret.first()
        if result is None:
            print  code[i], name[i], year, "年，stockreport数据库中无此股票！"
            bNeedWebData = True
        else: continue
        if bNeedWebData:
            if not bAccessWebData:
                url = "http://data.eastmoney.com/bbsj/stock"
                url += code[i]
                url += "/yjbb.html"
                print "读取东方财富年报数据......"
                data = urllib.urlopen(url).read()
                bAccessWebData = True
                print "东方财富年报数据读取完毕!"
                time.sleep(5)
            bs = bs4.BeautifulSoup(data,"lxml")
            body = bs.find('body')
            report = body.find_all('script')[9]
            reportString = report.string
            iPosStart = reportString.find('defjson:')
            report = reportString[iPosStart:]
            iPosStart = report.find('scode')
            iPosEnd = report.find('maketr')
            dataList = report[iPosStart:iPosEnd]
            rpList = dataList.split(",")
            strDate = sT.getDateString(year, 12, 30)
            for k in range(len(rpList)):
                if rpList[k].find(strDate[:7])!=-1:
                    eps = float(rpList[k+1][11:])
                    net_profits = float(rpList[k+6][18:])/10**4
                    profits_yoy = rpList[k+7][8:]
                    bvps = rpList[k+10][6:]
                    roe = rpList[k+9][14:]
                    epcf = rpList[k+11][11:]
                    sqlString = "select eps from stockreport_"
                    sqlString += "%s" % (year-1)
                    sqlString += "_4 "
                    sqlString += "where code="
                    sqlString += code[i]
                    ret = conn.execute(sqlString)
                    result = ret.first()
                    foundLastYearEPS = False
                    if result is not None:
                        foundLastYearEPS = True
                        epsLastYear = float(result.eps)
                    sqlString = "insert into stockreport_"
                    sqlString += "%s" %(year)
                    if foundLastYearEPS:
                        sqlString += "_4(code,name,eps,eps_yoy,bvps,roe,epcf,net_profits,profits_yoy) values('"
                    else:
                        sqlString += "_4(code,name,eps,bvps,roe,epcf,net_profits,profits_yoy) values('"
                    sqlString += code[i]
                    sqlString += "','"
                    sqlString += name[i]
                    sqlString += "',"
                    sqlString += "%s" %(eps)
                    sqlString += ","
                    if foundLastYearEPS:
                        sqlString += "%s" %(100*round((eps-epsLastYear)/epsLastYear,4))
                        sqlString += ","
                    sqlString += bvps
                    sqlString += ","
                    sqlString += roe
                    sqlString += ","
                    sqlString += epcf
                    sqlString += ","
                    sqlString += "%s" %(net_profits)
                    sqlString += ","
                    sqlString += profits_yoy
                    sqlString += ")"
                    conn.execute(sqlString)
                    print "已增加",code[i],name[i],"数据至",year,"年stockreport数据库"
                    break
print "年报数据检查完毕！"
print "开始检查每年分红情况..."
for i in range(count):
    bAccessDataFinished = False
    for year in range(STARTYEAR,ENDYEAR+1):
        sqlString = "select distrib,dividenTime from stockreport_"
        sqlString += "%s" %(year)
        sqlString += "_4 "
        sqlString += "where code="
        sqlString += code[i]
        ret = conn.execute(sqlString)
        result = ret.first()
        if result is None:
            print  code[i], name[i], year, "年，stockreport数据库中无此股票！"
            continue
        elif result.distrib is None or result.dividenTime is None:
            print  code[i], name[i], year, "年，stockreport数据库分红数据为空或分红日期为空！"
            if bAccessDataFinished==False:
                url = "http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/"
                url += code[i]
                url += ".phtml"
                print "读取新浪财经股票分红数据......"
                data = urllib.urlopen(url).read()
                print "新浪财经股票分红数据读取完毕！"
                time.sleep(5)
                bAccessDataFinished = True
            bs = bs4.BeautifulSoup(data,"lxml")
            table = bs.find_all('table')
            tableDividen = table[12]
            dividenHistory = tableDividen.find_all('tr')
            for idx in range(3,len(dividenHistory)):
                dividenDetail = dividenHistory[idx].find_all('td')
                yearWeb = unicode(dividenDetail[0].string)
                yearWeb = yearWeb[0:4]
                if str(year+1)==yearWeb: #网上的时间是实际分红时间要晚一年
                    sg =unicode(dividenDetail[1].string)
                    zg =unicode(dividenDetail[2].string)
                    px =unicode(dividenDetail[3].string)
                    dividenDate =unicode(dividenDetail[6].string)
                    if (u"0"!=sg or u"0"!=zg or u"0"!=px) and dividenDate != '--':
                        sqlString = "update stockreport_"
                        sqlString += "%s" % (year)
                        sqlString += "_4 "
                        sqlString += "set "
                        sqlString += "dividenTime='"
                        sqlString += dividenDate.encode('utf8')
                        sqlString += "'"
                        sqlString += ",distrib='10"
                        if px!=u"0":
                            sqlString += "派"
                            sqlString += px.encode('utf8')
                        if zg!=u"0":
                            sqlString += "转"
                            sqlString += zg.encode('utf8')
                        if sg!=u"0":
                            sqlString += "送"
                            sqlString += sg.encode('utf8')
                        sqlString += "' where code="
                        sqlString += code[i].encode('utf8')
                        ret = conn.execute(sqlString)
                    #else:
                        #sqlString = "update stockreport_"
                        #sqlString += "%s" % (year)
                        #sqlString += "_4 "
                        #sqlString += "set "
                        #sqlString += "dividenTime=null,distrib=null "
                        #sqlString += "where code="
                        #sqlString += code[i].encode('utf8')
                        #ret = conn.execute(sqlString)
                    print year, "10派", px, "转", zg, "送", sg,"，","分红日期：",dividenDate.encode('utf8')
print "每年分红情况检查完毕！"
print "*******************stockDataChecker检查完成！*******************"


