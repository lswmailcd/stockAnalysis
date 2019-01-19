#coding:utf-8

from sqlalchemy import create_engine
import tushare as ts
import time
import urllib
import bs4
import stockGlobalSpace as sG
import logRecoder as log

def createDBConnection():
    try:
        if  sG.bConnBD==False:
            sG.engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
            sG.dbConnection = sG.engine.connect()
            sG.bConnBD = True
            return sG.dbConnection
        else:
            return sG.dbConnection
    except Exception,e:
        print e
        exit(1)

def  validDate(month, day):
    if (day>0 and (day<32 and month in (1,3,5,7,8,10,12)) or (day<31 and month in (2,4,6,9,11)) or (month==2 and day<29)):
        return True
    return False

def getQuarter(m):
    if validDate(m,15)==False:
        return -1
    else:
        if m<4:
            return 1
        elif m<7:
            return 2
        elif m<10:
            return 3
        else:
            return 4

def splitDateString(date):
    year = date[:4]
    month = date[5:7]
    day = date[8:]
    return int(year),int(month),int(day)

def getDateString(year,month,day):
    date = "%s" % (year)
    date += "-"
    if month < 10:
        date += "0"
    date += "%s" % (month)
    date += "-"
    if day < 10:
        date += "0"
    date += "%s" % (day)
    return date

def getDistrib(distrib):#返回每股分红金额和转送股数
    nMoney = 0.0
    nStock = 0.0
    if distrib!=None:
        iPos0 = distrib.find("派")
        iPos1 = distrib.find("转")
        iPos2 = distrib.find("送")
        if iPos1>iPos2:
            temp = iPos1
            iPos1 = iPos2
            iPos2 = temp
        if iPos0!=-1: #有分红
            if iPos1==-1 and iPos2==-1: #无转送
                nMoney = float(distrib[iPos0+3:])
            elif iPos1!=-1 and iPos2==-1: #有转无送
                nMoney = float(distrib[iPos0+3:iPos1])
                nStock = float(distrib[iPos1+3:])
            elif iPos1==-1 and iPos2!=-1: #无转有送
                nMoney = float(distrib[iPos0+3:iPos2])
                nStock = float(distrib[iPos2+3:])
            else:#有转有送
                nMoney = float(distrib[iPos0+3:iPos1])
                nStock = float(distrib[iPos1+3:iPos2])
                nStock += float(distrib[iPos2+3:])
        else:#无分红
            if iPos1 != -1 and iPos2 == -1:  # 有转无送
                nStock = float(distrib[iPos1+3:])
            elif iPos1 == -1 and iPos2 != -1:  # 无转有送
                nStock = float(distrib[iPos2+3:])
            else:  # 有转有送
                nStock = float(distrib[iPos1+3:iPos2])
                nStock += float(distrib[iPos2+3:])
        #计算每股分红送转情况
        nMoney /=10.0
        nStock /=10.0
    return nMoney,nStock

def getStockNameByCode(code):
    conn = createDBConnection()
    sqlString = "select name from stockbasics_20190118 where code="
    sqlString += code
    ret = conn.execute(sqlString)
    if ret.rowcount == 0:
        print "代码", code, "有误，找不到该股票！"
        return None
    return ret.first().name

def getStockType(code):
    conn = createDBConnection()
    sqlString = "select stockType from stockindex "
    sqlString += "where code="
    sqlString += code
    ret = conn.execute(sqlString)
    if ret.rowcount == 0:
        print "代码", code, "有误，找不到该股票！"
        return ""
    return ret.first().stockType

def  getClosePriceForward(code, dORy, month=0, day=0, autp=None):#根据输入分开输入的年月日获取此日或此日前该月最近的一个交易日的收盘价
    foundData = False
    if month==0:#输入的日期在dORy中，以字符串形式输入
        y,m,d = splitDateString(dORy)
    else:
        y=dORy; m=month; d=day
    while foundData==False and validDate(m,d):
        date = getDateString(y, m, d)
        data = ts.get_k_data(code, start=date, end=date, autype=autp)
        if data.empty == False:
            foundData = True
        else:
            d -= 1
    if foundData == True:
        return foundData, data.values[0, 2], d
    else:
        return foundData,-1,d


def  getClosePrice(code, dORy, month=0, day=0, autp=None): #获取此日或此日后该月最近的一个交易日的收盘价
    foundData = False
    if month==0:#输入的日期在dORy中，以字符串形式输入
        y,m,d = splitDateString(dORy)
    else:
        y=dORy; m=month; d=day
    while foundData==False and validDate(m,d):
        date = getDateString(y, m, d)
        data = ts.get_k_data(code, start=date, end=date, autype=autp)
        if data.empty == False:
            foundData = True
        else:
            d += 1
            if not validDate(m, d):
                m += 1
                if m<13:
                    d = 1
                else:
                    break
    if foundData == True:
        return foundData, data.values[0, 2], m, d
    else:
        return foundData, -1, m, d

def getMarketType( code ):
    if code[:3] in ("600","601") : return "sh_main"
    if code[:3] in ("000","001") : return "sz_main"
    if code[:3]=="603" : return "sh_zxb"
    if code[:3] == "002": return "sz_zxb"
    if code[:3] == "300": return "sz_cyb"

def decodeEastMoneyNum(numCode):
    n = -1
    if( numCode=="ECEA" ):
        n = 0
    elif( numCode=="F2FF" ):
        n=1
    elif( numCode=="ECE9" ):
        n=2
    elif( numCode=="E426" ):
        n=3
    elif( numCode=="F2F8" ):
        n=4
    elif( numCode=="F137" ):
        n=5
    elif( numCode=="E273" ):
        n=6
    elif( numCode=="EBC0" ):
        n=7
    elif( numCode=="E268" ):
        n=8
    elif( numCode=="E793" ):
        n=9

    return n

def getEastMoneyData( strData ):
    str = strData.split(":")
    strList = str[1][1:-2].split(";")
    n = 0.0
    stageInt = True
    w = 10.0
    for s in strList:
        dPos = 3
        if  s[0]==".": #小数
            stageInt = False #进入小数处理
            dPos += 1
            w = 0.1

        if stageInt:
            n *= w
            n += decodeEastMoneyNum(s[dPos:])
        else:
            n += decodeEastMoneyNum(s[dPos:]) * w
            w *= 0.1

    return n

def checkStockReport(code, startYear, endYear):
    """

    :rtype: object
    """
    try:
        name, yearToMarket = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print code, name, yearToMarket,"年上市！"
        if yearToMarket>endYear:
            print code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!"
            return False
        if yearToMarket>startYear:
            print code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!"
            startYear = yearToMarket
        bNeedWebData = False
        bAccessWebData = False
        for year in range(startYear, endYear + 1):
            sqlString = "select code from stockreport_"
            sqlString += "%s" %(year)
            sqlString += "_4 "
            sqlString += "where code="
            sqlString += code
            conn = createDBConnection()
            ret = conn.execute(sqlString)
            result = ret.first()
            if result is None:
                print  code, name, year, "年，stockreport数据库中无此股票！"
                bNeedWebData = True
            else:
                continue
            if bNeedWebData:
                if not bAccessWebData:
                    url = "http://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/" #http://data.eastmoney.com/bbsj/yjbb/600887.html
                    url += code
                    url += "/ctrl/"
                    url += "%s" %(year)
                    url += "/displaytype/4.phtml"
                    print "读取新浪财经年报数据......"
                    data = urllib.urlopen(url).read()
                    print "新浪财经年报数据读取完毕!"
                    time.sleep(2)
                bs = bs4.BeautifulSoup(data,"lxml")
                body = bs.find('tbody')
                epsbody = body.find_all('tr')[3]
                eps = float(epsbody.find_all('td')[1].get_text())
                netprofitbody = body.find_all('tr')[32]
                net_profits = float(netprofitbody.find_all('td')[1].get_text())/10000.0
                profits_yoybody = body.find_all('tr')[35]
                profits_yoy = float(profits_yoybody.find_all('td')[1].get_text())
                bvpsbody = body.find_all('tr')[7]
                bvps = float(bvpsbody.find_all('td')[1].get_text())
                roebody = body.find_all('tr')[30]
                roe = float(roebody.find_all('td')[1].get_text())
                #epcf
                sqlString = "select eps from stockreport_"
                sqlString += "%s" % (year-1)
                sqlString += "_4 "
                sqlString += "where code="
                sqlString += code
                ret = conn.execute(sqlString)
                result = ret.first()
                foundLastYearEPS = False
                if result is not None:
                    foundLastYearEPS = True
                    epsLastYear = float(result.eps)
                    sqlString = "insert into stockreport_"
                    sqlString += "%s" %(year)
                    if foundLastYearEPS:
                        sqlString += "_4(code,name,eps,eps_yoy,bvps,roe,net_profits,profits_yoy) values('"
                    else:
                        sqlString += "_4(code,name,eps,bvps,roe,net_profits,profits_yoy) values('"
                    sqlString += code
                    sqlString += "','"
                    sqlString += name.decode('utf8')
                    sqlString += "',"
                    sqlString += "%s" %(eps)
                    sqlString += ","
                    if foundLastYearEPS:
                        sqlString += "%s" %(100*round((eps-epsLastYear)/epsLastYear,4))
                        sqlString += ","
                    sqlString += "%s" %(bvps)
                    sqlString += ","
                    sqlString += "%s" %(roe)
                    sqlString += ","
                    #sqlString += "%s" %(epcf)
                    #sqlString += ","
                    sqlString += "%s" %(net_profits)
                    sqlString += ","
                    sqlString += "%s" %(profits_yoy)
                    sqlString += ")"
                    conn.execute(sqlString)
                    log.writeUtfLog(sqlString.encode('utf8'))
                    print "已增加",code,name,"数据至",year,"年stockreport数据库"
    except Exception,e:
        print e
        exit(1)
    return True, startYear


def checkStockReportEastMoney(code, startYear, endYear):#EastMoney
    """

    :rtype: object
    """
    try:
        name, yearToMarket = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print code, name, yearToMarket,"年上市！"
        if yearToMarket>endYear:
            print code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!"
            return False
        if yearToMarket>startYear:
            print code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!"
            startYear = yearToMarket
        bNeedWebData = False
        bAccessWebData = False
        for year in range(startYear, endYear + 1):
            sqlString = "select code from stockreport_"
            sqlString += "%s" %(year)
            sqlString += "_4 "
            sqlString += "where code="
            sqlString += code
            conn = createDBConnection()
            ret = conn.execute(sqlString)
            result = ret.first()
            if result is None:
                print  code, name, year, "年，stockreport数据库中无此股票！"
                bNeedWebData = True
            else:
                continue
            if bNeedWebData:
                if not bAccessWebData:
                    url = "http://data.eastmoney.com/bbsj/yjbb/" #http://data.eastmoney.com/bbsj/yjbb/600887.html
                    url += code
                    url += ".html"
                    print "读取东方财富年报数据......"
                    data = urllib.urlopen(url).read()
                    bAccessWebData = True
                    print "东方财富年报数据读取完毕!"
                    time.sleep(2)
                bs = bs4.BeautifulSoup(data,"lxml")
                body = bs.find('body')
                report = body.find_all('script')[12]
                reportString = report.string
                iPosStart = reportString.find('defjson:')
                report = reportString[iPosStart:]
                iPosStart = report.find('scode')
                iPosEnd = report.find('maketr')
                dataList = report[iPosStart:iPosEnd]
                rpList = dataList.split(",")
                strDate = getDateString(year, 12, 30)
                for k in range(len(rpList)):
                    if rpList[k].find(strDate[:7])!=-1:
                        eps = getEastMoneyData(rpList[k+5])
                        net_profits = getEastMoneyData(rpList[k+10])/10000.0
                        profits_yoy = getEastMoneyData(rpList[k+11])
                        bvps = getEastMoneyData(rpList[k+14])
                        roe = getEastMoneyData(rpList[k+13])
                        epcf = getEastMoneyData(rpList[k+15])
                        sqlString = "select eps from stockreport_"
                        sqlString += "%s" % (year-1)
                        sqlString += "_4 "
                        sqlString += "where code="
                        sqlString += code
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
                        sqlString += code
                        sqlString += "','"
                        sqlString += name.decode('utf8')
                        sqlString += "',"
                        sqlString += "%s" %(eps)
                        sqlString += ","
                        if foundLastYearEPS:
                            sqlString += "%s" %(100*round((eps-epsLastYear)/epsLastYear,4))
                            sqlString += ","
                        sqlString += "%s" %(bvps)
                        sqlString += ","
                        sqlString += "%s" %(roe)
                        sqlString += ","
                        sqlString += "%s" %(epcf)
                        sqlString += ","
                        sqlString += "%s" %(net_profits)
                        sqlString += ","
                        sqlString += "%s" %(profits_yoy)
                        sqlString += ")"
                        conn.execute(sqlString)
                        log.writeUtfLog(sqlString.encode('utf8'))
                        print "已增加",code,name,"数据至",year,"年stockreport数据库"
                        break
    except Exception,e:
        print e
        exit(1)
    return True, startYear

def getStockBasics(code):
    try:
        sqlString = "select name, timetomarket from stockbasics_20190118 "
        sqlString += "where code="
        sqlString += code
        conn = createDBConnection()
        ret = conn.execute(sqlString)
        result = ret.first()
    except Exception,e:
        print e
        exit(1)
    if result is None :
        print  code, "股票基本数据获取失败！"
        return "", 0
    elif result.timetomarket == 0:
        print  code, result.name,"股票上市时间数据为空！"
        return  result.name, 0
    return  result.name, int(result.timetomarket / 1E4)

def checkDistrib(code, startYear, endYear):
    try:
        date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        y,m,d = splitDateString(date)
        bAccessDataFinished = False
        for year in range(startYear, endYear + 1):
            sqlString = "select name,distrib,dividenTime from stockreport_"
            sqlString += "%s" % (year)
            sqlString += "_4 "
            sqlString += "where code="
            sqlString += code
            conn = createDBConnection()
            ret = conn.execute(sqlString)
            result = ret.first()
            if result is None:
                print  code, year, "年，stockreport数据库中无此股票！"
                exit(1)
            elif result.distrib is None or  result.dividenTime is None:
                name = result.name
                print  code, name, year, "年，stockreport数据库分红数据为空或分红日期为空！"
                if bAccessDataFinished == False:
                    url = "http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/"
                    url += code
                    url += ".phtml"
                    print "读取新浪财经股票分红数据......"
                    data = urllib.urlopen(url).read()
                    print "新浪财经股票分红数据读取完毕！"
                    time.sleep(5)
                    bAccessDataFinished = True
                bs = bs4.BeautifulSoup(data, "lxml")
                div = bs.find("div")
                table = div.find_all("table")[13]
                tbody = table.find_all("tbody")[0]
                tds = tbody.find_all("td")
                for i in range(0, len(tds)):
                    if(tds[i].string==u"实施"):
                        y,m,d = splitDateString(tds[i + 2].string)
                        if y<startYear: break
                        if year + 1 == y: # 网上的时间是实际分红时间要晚一年
                            sg = unicode(tds[i - 3].string)
                            zg = unicode(tds[i - 2].string)
                            px = unicode(tds[i - 1].string)
                            dividenDate = unicode(tds[i + 2].string)
                            if (u"0" != sg or u"0" != zg or u"0" != px) and dividenDate != '--':
                                sqlString = "update stockreport_"
                                sqlString += "%s" % (year)
                                sqlString += "_4 "
                                sqlString += "set "
                                sqlString += "dividenTime='"
                                sqlString += dividenDate.encode('utf8')
                                sqlString += "'"
                                sqlString += ",distrib='10"
                                if px != u"0":
                                    sqlString += "派"
                                    sqlString += px.encode('utf8')
                                if zg != u"0":
                                    sqlString += "转"
                                    sqlString += zg.encode('utf8')
                                if sg != u"0":
                                    sqlString += "送"
                                    sqlString += sg.encode('utf8')
                                sqlString += "' where code="
                                sqlString += code.encode('utf8')
                                ret = conn.execute(sqlString)
                                log.writeUtfLog(sqlString)
                            # else:
                            # sqlString = "update stockreport_"
                            # sqlString += "%s" % (year)
                            # sqlString += "_4 "
                            # sqlString += "set "
                            # sqlString += "dividenTime=null,distrib=null "
                            # sqlString += "where code="
                            # sqlString += code[i].encode('utf8')
                            # ret = conn.execute(sqlString)
                            print year, "10派", px, "转", zg, "送", sg, "，", "分红登记日期：", dividenDate.encode('utf8')
    except Exception,e:
        print e
        exit(1)
    return True