import pymysql
pymysql.install_as_MySQLdb()    #手动指定将MySQLdb转给pymysql处理
from sqlalchemy import create_engine
import tushare as ts
import time
import re
import urllib
import bs4
import stockGlobalSpace as sG
import logRecoder as log
from stockCalender import stockCalender
import pandas as pd


def createTushare():
    try:
        if  sG.Tushare is None:
            ts.set_token('af19674c38f5c197b7bfc96e5353166998c66717ae9e82b6cc371ca2')
            sG.Tushare = ts.pro_api()
            return sG.Tushare
        else:
            return sG.Tushare
    except Exception as e:
        print(e)
        exit(1)


def createCalender():
    try:
        if  sG.Calender is None:
            sG.Calender = stockCalender()
            return sG.Calender
        else:
            return sG.Calender
    except Exception as e:
        print(e)
        exit(1)

def createDBConnection():
    try:
        if  sG.bConnBD==False:
            sG.lock.acquire()
            sG.engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
            sG.dbConnection = sG.engine.connect()
            sG.lock.release()
            sG.bConnBD = True
            return sG.dbConnection
        else:
            return sG.dbConnection
    except Exception as e:
        print(e)
        sG.lock.release()
        exit(1)

def parseDistrib(distrib):#返回每股分红金额和转送股数
    nMoney = 0.0
    nStock = 0.0
    listSZ=[]
    if distrib!=None:
        d = distrib.replace("派","-")
        d = d.replace("送", "-")
        d = d.replace("转", "-")
        dlist = d.split("-")
        dlist =[float(x) for x in dlist]

        pos = distrib.find("派")
        if pos!=-1: nMoney = dlist[1]

        listSZ.append(distrib.find("送"))
        listSZ.append(distrib.find("转"))
        if listSZ.count(-1) == 1: nStock=dlist[-1]
        elif listSZ.count(-1) == 0: nStock = sum(dlist[-2:])

        #计算每股分红送转情况
        nMoney /=10.0
        nStock /=10.0
    return nMoney,nStock

def getStockNameByCode(code):
    conn = createDBConnection()
    sqlString = "select name from stockbasics where code="
    sqlString += code
    ret = conn.execute(sqlString)
    if ret.rowcount == 0:
        print("代码", code, "有误，找不到该股票！")
        return None
    return ret.first().name

def getStockType(code):
    conn = createDBConnection()
    sqlString = "select stockType from stockindex "
    sqlString += "where code="
    sqlString += code
    ret = conn.execute(sqlString)
    if ret.rowcount == 0:
        print("代码", code, "有误，找不到该股票！")
        return ""
    return ret.first().stockType


def  getClosePriceForward(code, dORy, month=0, day=0):#获取当年此月或此月以前最近的收盘价
    if month==0:#输入的日期在dORy中，以字符串形式输入
        date = dORy
    else:
        date = getDateString(dORy, month, day)

    sqlString = "select min(date) as sd, max(date) as ed from stockprice where code='{}'".format(code)
    conn = createDBConnection()
    try:
        ret = conn.execute(sqlString)
        r = ret.first()
        if r.sd is None:
            print("getClosePriceBackward()出错！，请检查 {} 股票价格是否存在！".format(code))
            exit(1)
    except Exception as e:
        print(e,"数据表stockprice访问出错！")
        return False, -1, None

    if date<r.sd:
        print("获取的日期小于{}，请检查是否获得最新股价数据！".format(r.sd,r.ed))
        return False, -1, None
    else:
        if date >r.ed: date=r.ed
        sqlString = "select closeprice, date from stockprice where code='{}' and date='{}'".format(code, date)
        try:
            ret = conn.execute(sqlString)
            r = ret.first()
        except Exception as e:
            print(e, "数据表stockprice访问出错！")
            return False, -1, None
        if r:
            return True, r.closeprice, r.date
        else:#所找股票价格的日期不在stockprice当前股票价格日期中
            sqlString = "select closeprice, date from stockprice where code='{}' and date<'{}' order by date desc limit 1".format(code, date)
            try:
                ret = conn.execute(sqlString)
                r = ret.first()
            except Exception as e:
                print(e, "数据表stockprice访问出错！")
                return False, -1, None
            if r:
                return True, r.closeprice, r.date

    return False, -1, None

def getClosePrice(code, dORy, month=0, day=0, autp=None):
    if month==0:#输入的日期在dORy中，以字符串形式输入
        y,m,d = splitDateString(dORy)
    else:
        y=dORy; m=month; d=day
    if createCalender().validDate(y,m,d):
        date = getDateString(y, m, d)
        conn = createDBConnection()
        sqlString = "select closeprice from stockprice where code="
        sqlString += code
        sqlString += " and date='"
        sqlString += date
        sqlString += "'"
        try:
            ret = conn.execute(sqlString)
            result = ret.first()
        except Exception as e:
            print(e)
        if result is not None and result.closeprice is not None:
            return True, result.closeprice
        else:
            return False, -1
    return False, -1


def  getClosePriceBackward(code, dORy, month=0, day=0): #获取此日或此日后该月最近的一个交易日的收盘价
    if month==0:#输入的日期在dORy中，以字符串形式输入
        date = dORy
    else:
        date = getDateString(dORy, month, day)

    sqlString = "select min(date) as sd, max(date) as ed from stockprice where code='{}'".format(code)
    conn = createDBConnection()
    try:
        ret = conn.execute(sqlString)
        r = ret.first()
        if r.sd is None:
            print("getClosePriceBackward()出错！，请检查 {} 股票价格是否存在！".format(code))
            exit(1)
    except Exception as e:
        print(e,"数据表stockprice访问出错！")
        return False, -1, None

    if date>r.ed:
        print("获取的日期{}不在时间范围：{}---{}内，请检查是否获得最新股价数据！".format(date, r.sd, r.ed))
        return False, -1, None
    else:
        if date<r.sd: date = r.sd
        sqlString = "select closeprice,date from stockprice where code='{}' and date='{}'".format(code, date)
        try:
            ret = conn.execute(sqlString)
            r = ret.first()
        except Exception as e:
            print(e, "数据表stockprice访问出错！")
            return False, -1, None
        if r:
            return True, r.closeprice, r.date
        else:#所找股票价格的日期不在stockprice当前股票价格日期中
            sqlString = "select closeprice, date from stockprice where code='{}' and date>'{}' order by date asc limit 1".format(code, date)
            try:
                ret = conn.execute(sqlString)
                r = ret.first()
            except Exception as e:
                print(e, "数据表stockprice访问出错！")
                return False, -1, None
            if r:
                return True, r.closeprice, r.date

    return False, -1, None

def getStockEPSTTM(code, year, quarter):
    if quarter == 4:
        return getStockEPS(code,year,quarter)
    elif quarter==3:
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData_Q3, EPS_Q3 = getStockEPS(code, year, 3)
        totalStockQ3 = getStockCountQuarter(code, year, 3)
        foundData_LQ4, EPS_LQ4 = getStockEPS(code, year-1, 4)
        totalStockLQ4 = getStockCountQuarter(code, year-1, 4)
        foundData_LQ3, EPS_LQ3 = getStockEPS(code, year-1, 3)
        totalStockLQ3 = getStockCountQuarter(code, year-1, 3)
        if foundData_Q3:
            return True, (EPS_Q3*totalStockQ3 + EPS_LQ4*totalStockLQ4 - EPS_LQ3*totalStockLQ3)/totalStockQ3
    elif quarter == 2:
        # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
        foundData_Q2, EPS_Q2 = getStockEPS(code, year, 2)
        totalStockQ2 = getStockCountQuarter(code, year, 2)
        foundData_LQ4, EPS_LQ4 = getStockEPS(code, year - 1, 4)
        totalStockLQ4 = getStockCountQuarter(code, year - 1, 4)
        foundData_LQ2, EPS_LQ2 = getStockEPS(code, year - 1, 2)
        totalStockLQ2 = getStockCountQuarter(code, year - 1, 2)
        if foundData_Q2:
            return True, (EPS_Q2*totalStockQ2 + EPS_LQ4*totalStockLQ4 - EPS_LQ2*totalStockLQ2)/totalStockQ2
    else:
        # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
        foundData_Q1, EPS_Q1 = getStockEPS(code, year, 1)
        totalStockQ1 = getStockCountQuarter(code, year, 1)
        foundData_LQ4, EPS_LQ4 = getStockEPS(code, year - 1, 4)
        totalStockLQ4 = getStockCountQuarter(code, year - 1, 4)
        foundData_LQ1, EPS_LQ1 = getStockEPS(code, year - 1, 1)
        totalStockLQ1 = getStockCountQuarter(code, year - 1, 1)
        if foundData_Q1:
            return True, (EPS_Q1*totalStockQ1 + EPS_LQ4*totalStockLQ4 - EPS_LQ1*totalStockLQ1)/totalStockQ1

    return False, 0

def getStockEPSdiscountTTM(code, year, quarter):
    if quarter == 4:
        return getStockEPSdiscount(code,year,quarter)
    elif quarter==3:
        #epsTTM = 当年3季报eps+去年4季报eps-去年3季报eps
        foundData_Q3, EPS_Q3 = getStockEPSdiscount(code, year, 3)
        totalStockQ3 = getStockCountQuarter(code, year, 3)
        foundData_LQ4, EPS_LQ4 = getStockEPSdiscount(code, year-1, 4)
        totalStockLQ4 = getStockCountQuarter(code, year-1, 4)
        foundData_LQ3, EPS_LQ3 = getStockEPSdiscount(code, year-1, 3)
        totalStockLQ3 = getStockCountQuarter(code, year-1, 3)
        if foundData_Q3:
            return True, (EPS_Q3*totalStockQ3 + EPS_LQ4*totalStockLQ4 - EPS_LQ3*totalStockLQ3)/totalStockQ3
    elif quarter == 2:
        # epsTTM = 当年2季报eps+去年4季报eps-去年2季报eps
        foundData_Q2, EPS_Q2 = getStockEPSdiscount(code, year, 2)
        totalStockQ2 = getStockCountQuarter(code, year, 2)
        foundData_LQ4, EPS_LQ4 = getStockEPSdiscount(code, year - 1, 4)
        foundData_LQ2, EPS_LQ2 = getStockEPSdiscount(code, year - 1, 2)
        totalStockLQ4 = getStockCountQuarter(code, year - 1, 4)
        totalStockLQ2 = getStockCountQuarter(code, year - 1, 2)
        if foundData_Q2:
            return True, (EPS_Q2*totalStockQ2 + EPS_LQ4*totalStockLQ4 - EPS_LQ2*totalStockLQ2)/totalStockQ2
    else:
        # epsTTM = 当年1季报eps+去年4季报eps-去年1季报eps
        foundData_Q1, EPS_Q1 = getStockEPSdiscount(code, year, 1)
        totalStockQ1 = getStockCountQuarter(code, year, 1)
        foundData_LQ4, EPS_LQ4 = getStockEPSdiscount(code, year - 1, 4)
        foundData_LQ1, EPS_LQ1 = getStockEPSdiscount(code, year - 1, 1)
        totalStockLQ4 = getStockCountQuarter(code, year-1, 4)
        totalStockLQ1 = getStockCountQuarter(code, year-1, 1)
        if foundData_Q1:
            return True, (EPS_Q1*totalStockQ1 + EPS_LQ4*totalStockLQ4 - EPS_LQ1*totalStockLQ1)/totalStockQ1

    return False, 0

def getStockEPSdiscount(code, year, quarter):#获取扣非EPS
    sqlString = "select eps_discount from stockreport_sup_"
    sqlString += "%s" % (year)
    sqlString += "_"
    sqlString += "%s" % (quarter)
    sqlString += " where code="
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
        result = ret.first()
    except Exception as e:
        return False, 0
    if result is None or result.eps_discount== 0.0 or result.eps_discount==sG.sNINF:#如果有eps_discount没有找到数据，则查找扣非总利润计算扣非EPS
        sqlString = "select net_profits_discount from stockreport_sup_"
        sqlString += "%s" % (year)
        sqlString += "_"
        sqlString += "%s" % (quarter)
        sqlString += " where code="
        sqlString += code
        sqlString1 = "select gb from asset_debt_"
        sqlString1 += "%s" % (year)
        sqlString1 += "_"
        sqlString1 += "%s" % (quarter)
        sqlString1 += " where code="
        sqlString1 += code
        try:
            ret = conn.execute(sqlString)
            result = ret.first()
            ret1 = conn.execute(sqlString1)
            result1 = ret1.first()
        except Exception as e:
            return False, sG.sNINF
        if (result is None or result.net_profits_discount is None) or (result1 is None or result1.gb is None):
            print(code, getStockNameByCode(code), year, u"年", quarter, u"季度", u"stockreport_sup数据库中无此股票DiscountEPS信息!")
            return False, sG.sNINF
        else:#通过扣非利润计算每股扣非，并填空eps_discount列
            EPSdiscount = result.net_profits_discount / result1.gb
            sqlString = "update stockreport_sup_"
            sqlString += "%s" % (year)
            sqlString += "_"
            sqlString += "%s " % (quarter)
            sqlString += "set eps_discount=%s" % (EPSdiscount)
            sqlString += " where code="
            sqlString += code
            try:
                conn.execute(sqlString)
            except Exception as e:
                return False, 0
            return True, EPSdiscount
    else:
        return True, result.eps_discount

def getStockEPS(code, year, quarter):#获取基本EPS
    sqlString = "select eps from stockreport_"
    sqlString += "%s" % (year)
    sqlString += "_"
    sqlString += "%s" % (quarter)
    sqlString += " where code="
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
        result = ret.first()
    except Exception as e:
        return False, 0
    if result is None or result.eps is None:
        print(code, getStockNameByCode(code), year, u"年", quarter, u"季度", u"stockreport数据库中无此股票!")
        return False, 0
    else:
        return True, result.eps

#有股本数据时，返回当前季度股本；没有股本数据时，返回0.0
def getStockCountQuarter(code, year, quarter):
    #获取股本
    sqlString = "select gb from asset_debt_"
    sqlString += "%s" % (year)
    sqlString += "_%s where code=" %(quarter)
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
    except Exception as e:
        print(code, year, '年',quarter,"季度，获取股本数据,asset_debt数据库访问失败！")
        return 0.0
    result = ret.first()
    if result is None or result.gb is None:
        print(code, year, "年",quarter, "季度，asset_debt资产负债表股本数据获取失败！")
        return 0.0
    else:
        return result.gb

def getDividenTime(code, year):#取得股权登记日，为分红日的前一天
    sqlString = "select dividentime from stockreport_sup_"
    sqlString += "%s_4" % year
    sqlString += " where code="
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
    except Exception as e:
        print(e)
        print(code, year, "年，stockreport_sup数据表:访问失败！")
    result = ret.first()
    if result is None or result.dividentime is None:
        print(code, year, "年，stockreport_sup表:分红日期数据获取失败,此年可能无分红！")
        return False, None
    return True, result.dividentime

def getDistrib(code, year):
    sqlString = "select distrib from stockreport_"
    sqlString += "%s_4" % year
    sqlString += " where code="
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
    except Exception as e:
        print(e)
        print(code, year, "年，stockreport数据表:访问失败！")
        return False, None
    result = ret.first()
    if result is None or result.distrib is None:
        print(code, year, "年，stockreport表:分红数据获取失败,此年可能无分红！")
        return False, None
    else:
        money, stock = parseDistrib(result.distrib)
        return True, money, stock


def getStockCount(code, dORy, month=0, day=0):
    if month==0:#输入的日期在dORy中，以字符串形式输入
        y,m,d = splitDateString(dORy)
    else:
        y=dORy; m=month; d=day
    quarter = createCalender().getQuarter(m)
    #查找是否存在转股
    #检查去年末的股数
    gblast = getStockCountQuarter(code,y-1,4)
    # 获取当前季度的股本
    gb = getStockCountQuarter(code, y, quarter)
    if gblast!=gb:#去年末和当前季度存在股数变化
        found, dividenTime = getDividenTime(code, y - 1)
        if found and dividenTime >= getDateString(y, m, d):  # 去年有分红且当前日期还没有分红送股
            gb = gblast
    if abs(gb)<0.001:#本年本季度股本数据没有找到
        gb = gblast
        found, dividenTime = getDividenTime(code, y-1)
        if found and dividenTime<getDateString(y,m,d):#去年有分红且当前日期已经分了红了，要检查是否有送转股数
            found, money, stock = getDistrib(code, y-1)
            if found and stock>0.0: #去年有分红且有送转股
                gb = (1+stock)*gblast

    return gb

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

def checkStockAssetDebt(code, startYear, endYear):

    def getData(items):
        dataList = []
        for item in items:
            if item.get_text() == '--':
                dataList.append(sG.sNINF)
            else:
                dataList.append(float(item.get_text().replace(',', '')))
        return dataList

    def findRow(row, rowname, items):
        if row.find('a', {'target': '_blank'}) \
                and row.find('a', {'target': '_blank'}).get_text() == rowname:
            result = row.findAll('td', {'style': re.compile(r'text.*')})
            for r in result:
                items.append(r)
            return True
        else:
            return False

    try:
        name, yearToMarket,_,_ = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print(code, name, yearToMarket,"年上市！")
        if yearToMarket>endYear:
            print(code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!")
            return False
        if yearToMarket>startYear:
            print(code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!")
            startYear = yearToMarket
        for year in range(startYear, endYear + 1):
            bTableExit=[True, True, True, True] #数据库中资产负债表是否已存在，初始值为True存在
            bDataExit=[True, True, True, True] #资产负债表中的数据是否已存在，初始值为True存在
            for Qt in range(1,5):
                sqlString = "select code from asset_debt_"
                sqlString += "%s" %(year)
                sqlString += "_%s " %(Qt)
                sqlString += "where code="
                sqlString += code
                conn = createDBConnection()
                try:
                    ret = conn.execute(sqlString)
                except Exception as e:
                    bTableExit[Qt-1]=False
                    print(code, name, year, "年", Qt, "季度，asset_debt数据表不存在！")
                    continue
                result = ret.first()
                if result is None:
                    bDataExit[Qt-1] = False
                    print(code, name, year, "年", Qt, "季度，asset_debt数据表中无此股票！")
                else:
                    continue
            if bDataExit.count(False)>0:
                url = "http://money.finance.sina.com.cn/corp/go.php/vFD_BalanceSheet/stockid/"  # http://data.eastmoney.com/bbsj/yjbb/600887.html
                url += code
                url += "/ctrl/"
                url += "%s" % (year)
                url += "/displaytype/4.phtml"
                try:
                    print( "读取新浪财经资产负债表数据......")
                    response = urllib.request.urlopen(url=url)
                    data = response.read().decode("gbk")
                    print( "新浪财经资产负债表数据读取完毕!")
                    time.sleep(2)
                except Exception as e:
                    print(code, name, year, "年，新浪财经资产负债表数据不存在！")
                    continue
                bs = bs4.BeautifulSoup(data, "lxml")
                tb = bs.find('table',{'id':'BalanceSheetNewTable0'})
                rows = tb.find('tbody').findAll('tr')
                Qt = 0
                for row in rows:
                    items = []
                    if row.find('strong') and row.find('strong').get_text()==u'报表日期':
                        Qt = len(row.findAll('td'))-1
                    elif findRow(row, u'应收账款',items): yszk = getData(items)
                    elif findRow(row, u'其他应收款', items): yszk2 = getData(items)
                    elif findRow(row, u'存货', items): ch = getData(items)
                    elif findRow(row, u'流动资产合计', items): ldzc = getData(items)
                    elif findRow(row, u'非流动资产合计', items): gdzc = getData(items)
                    elif findRow(row, u'流动负债合计', items): ldfz = getData(items)
                    elif findRow(row, u'非流动负债合计', items): gdfz = getData(items)
                    elif findRow(row, u'实收资本(或股本)', items): gb = getData(items)
                    elif findRow(row, u'所有者权益(或股东权益)合计', items): gdqy = getData(items)
                #将获取的数据插入数据表asset_debt
                for i in range(1,Qt+1):
                    if bDataExit[i-1]==False:#数据有缺失时，由前代码的逻辑必然数据表存在
                        sqlString = "insert into asset_debt_"
                        sqlString += "%s" % (year)
                        sqlString += "_%s" % (i)
                        sqlString += "(code,name,yszk,yszk2,ch,ldzc,gdzc,ldfz,gdfz,gb,gdqy) values('"
                        sqlString += code
                        sqlString += "','"
                        sqlString += name
                        sqlString += "',"
                        sqlString += "%s" % (yszk[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (yszk2[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (ch[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (ldzc[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (gdzc[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (ldfz[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (gdfz[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (gb[Qt-i])
                        sqlString += ","
                        sqlString += "%s" % (gdqy[Qt-i])
                        sqlString += ")"
                        conn.execute(sqlString)
                        log.writeUtfLog(sqlString)
                        print( "已增加", code, name, "数据至", year, "年",i,"季度asset_debt数据表")
    except Exception as e:
        print(e)
        exit(1)

def checkStockAssetDebt_BACKUP(code, startYear, endYear):
    try:
        name, yearToMarket,_,_ = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print(code, name, yearToMarket,"年上市！")
        if yearToMarket>endYear:
            print(code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!")
            return False
        if yearToMarket>startYear:
            print(code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!")
            startYear = yearToMarket
        for year in range(startYear, endYear + 1):
            bTableExit=[True, True, True, True] #数据库中资产负债表是否已存在，初始值为True存在
            bDataExit=[True, True, True, True] #资产负债表中的数据是否已存在，初始值为True存在
            for Qt in range(1,5):
                sqlString = "select code from asset_debt_"
                sqlString += "%s" %(year)
                sqlString += "_%s " %(Qt)
                sqlString += "where code="
                sqlString += code
                conn = createDBConnection()
                try:
                    ret = conn.execute(sqlString)
                except Exception as e:
                    bTableExit[Qt-1]=False
                    print(code, name, year, "年", Qt, "季度，asset_debt数据表不存在！")
                    continue
                result = ret.first()
                if result is None:
                    bDataExit[Qt-1] = False
                    print(code, name, year, "年", Qt, "季度，asset_debt数据表中无此股票！")
                else:
                    continue
            if bDataExit.count(False)>0:
                url = "http://money.finance.sina.com.cn/corp/go.php/vFD_BalanceSheet/stockid/"  # http://data.eastmoney.com/bbsj/yjbb/600887.html
                url += code
                url += "/ctrl/"
                url += "%s" % (year)
                url += "/displaytype/4.phtml"
                print("读取新浪财经资产负债表数据......")
                data = urllib.urlopen(url).read().decode("gbk")
                print("新浪财经资产负债表数据读取完毕!")
                time.sleep(2)
                bs = bs4.BeautifulSoup(data, "lxml")
                body = bs.find('tbody')
                try:
                    datebody = body.find_all('tr')[0]
                except Exception as e:
                    print(code, name, year, "年", Qt, "季度，新浪财经资产负债表数据不存在！")
                    continue
                year,month,day = splitDateString(datebody.find_all('td')[1].get_text())
                Qt = 5
                if month == 3: Qt = 2
                elif month == 6: Qt = 3
                elif month == 9: Qt = 4
                yszkbody = body.find_all('tr')[8]
                yszk = []
                for i in range(1,Qt):
                    yszkStr = yszkbody.find_all('td')[i].get_text()
                    if yszkStr == '--':
                        yszk.append(sG.sNINF)
                    else:
                        yszk.append(float(yszkStr.replace(',','')))
                yszk2body = body.find_all('tr')[12]
                yszk2 = []
                for i in range(1, Qt):
                    yszk2Str = yszk2body.find_all('td')[i].get_text()
                    if yszk2Str == '--':
                        yszk2.append(sG.sNINF)
                    else:
                        yszk2.append(float(yszk2Str.replace(',','')))
                chbody = body.find_all('tr')[14]
                ch = []
                for i in range(1, Qt):
                    chStr = chbody.find_all('td')[i].get_text()
                    if chStr == '--':
                        ch.append(sG.sNINF)
                    else:
                        ch.append(float(chStr.replace(',','')))
                ldzcbody = body.find_all('tr')[20]
                ldzc = []
                for i in range(1, Qt):
                    ldzcStr = ldzcbody.find_all('td')[i].get_text()
                    if ldzcStr == '--':
                        ldzc.append(sG.sNINF)
                    else:
                        ldzc.append(float(ldzcStr.replace(',','')))
                gdzcbody = body.find_all('tr')[41]
                gdzc = []
                for i in range(1, Qt):
                    gdzcStr = gdzcbody.find_all('td')[i].get_text()
                    if gdzcStr == '--':
                        gdzc.append(sG.sNINF)
                    else:
                        gdzc.append(float(gdzcStr.replace(',','')))
                ldfzbody = body.find_all('tr')[61]
                ldfz = []
                for i in range(1, Qt):
                    ldfzStr = ldfzbody.find_all('td')[i].get_text()
                    if ldfzStr == '--':
                        ldfz.append(sG.sNINF)
                    else:
                        ldfz.append(float(ldfzStr.replace(',','')))
                gdfzbody = body.find_all('tr')[72]
                gdfz = []
                for i in range(1, Qt):
                    gdfzStr = gdfzbody.find_all('td')[i].get_text()
                    if gdfzStr == '--':
                        gdfz.append(sG.sNINF)
                    else:
                        gdfz.append(float(gdfzStr.replace(',','')))
                gbbody = body.find_all('tr')[75]
                gb = []
                for i in range(1, Qt):
                    gbStr = gbbody.find_all('td')[i].get_text()
                    if gbStr == '--':
                        gb.append(sG.sNINF)
                    else:
                        gb.append(float(gbStr.replace(',','')))
                gdqybody = body.find_all('tr')[85]
                gdqy = []
                for i in range(1, Qt):
                    gdqyStr = gdqybody.find_all('td')[i].get_text()
                    if gdqyStr == '--':
                        gdqy.append(sG.sNINF)
                    else:
                        gdqy.append(float(gdqyStr.replace(',','')))
                #将获取的数据插入数据表asset_debt
                for i in range(1,Qt):
                    if bDataExit[i-1]==False:#数据有缺失时，由前代码的逻辑必然数据表存在
                        sqlString = "insert into asset_debt_"
                        sqlString += "%s" % (year)
                        sqlString += "_%s" % (i)
                        sqlString += "(code,name,yszk,yszk2,ch,ldzc,gdzc,ldfz,gdfz,gb,gdqy) values('"
                        sqlString += code
                        sqlString += "','"
                        sqlString += name.decode('utf8')
                        sqlString += "',"
                        sqlString += "%s" % (yszk[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (yszk2[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (ch[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (ldzc[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (gdzc[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (ldfz[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (gdfz[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (gb[Qt-1-i])
                        sqlString += ","
                        sqlString += "%s" % (gdqy[Qt-1-i])
                        sqlString += ")"
                        conn.execute(sqlString)
                        log.writeUtfLog(sqlString.encode('utf8'))
                        print("已增加", code, name, "数据至", year, "年",i,"季度asset_debt数据表")
    except Exception as e:
        print(e)
        exit(1)

def checkStockReport(code, startYear, endYear):
    """

    :rtype: object
    """

    def getData(items):
        dataList = []
        for item in items:
            if item.get_text() == '--':
                dataList.append(sG.sNINF)
            else:
                dataList.append(float(item.get_text().replace(',', '')))
        return dataList

    def findRow(row, rowname, items):
        if row.find('a', {'target': '_blank'}) \
                and row.find('a', {'target': '_blank'}).get_text() == rowname:
            result = row.findAll('td')
            for i in range(1, len(result)):
                items.append(result[i])
            return True
        else:
            return False

    try:
        name, yearToMarket,_,_ = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print(code, name, yearToMarket,"年上市！")
        if yearToMarket>endYear:
            print(code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!")
            return False
        if yearToMarket>startYear:
            print(code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!")
            startYear = yearToMarket
        for year in range(startYear, endYear + 1):
            #bTableExit=[True, True, True, True] #数据库中stockreport业绩报表是否已存在，初始值为True存在
            bDataExit=[True, True, True, True] #stockreport业绩报表中的数据是否已存在，初始值为True存在
            #bTableSupExist = [True, True, True, True]#数据库中stockreport_sup业绩报表是否已存在，初始值为True存在
            bDataSupExist = [True, True, True, True]#stockreport_sup业绩报表中的数据是否已存在，初始值为True存在
            for Qt in range(1, 5):
                sqlString = "select code from stockreport_"
                sqlString += "%s" %(year)
                sqlString += "_%s " % (Qt)
                sqlString += "where code="
                sqlString += code
                conn = createDBConnection()
                try:
                    ret = conn.execute(sqlString)
                except Exception as e:
                    #bTableExit[Qt-1]=False
                    print(code, name, year, "年", Qt, "季度，stockreport数据表不存在！")
                    continue
                result = ret.first()
                if result is None:
                    bDataExit[Qt-1] = False
                    print(code, name, year, "年", Qt, "季度，stockreport数据表中无此股票！")
                else:
                    continue
            for Qt in range(1, 5):
                sqlString = "select code from stockreport_sup_"
                sqlString += "%s" %(year)
                sqlString += "_%s " % (Qt)
                sqlString += "where code="
                sqlString += code
                conn = createDBConnection()
                try:
                    ret = conn.execute(sqlString)
                except Exception as e:
                    #bTableSupExist[Qt-1]=False
                    print(code, name, year, "年", Qt, "季度，stockreport_sup数据表不存在！")
                    continue
                result = ret.first()
                if result is None:
                    bDataSupExist[Qt-1] = False
                    print(code, name, year, "年", Qt, "季度，stockreport_sup数据表中无此股票！")
                else:
                    continue
            if bDataExit.count(False)>0 or bDataSupExist.count(False)>0:
                url = "http://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/" #http://data.eastmoney.com/bbsj/yjbb/600887.html
                url += code
                url += "/ctrl/"
                url += "%s" %(year)
                url += "/displaytype/4.phtml"
                try:
                    print("读取新浪财经财务指标......")
                    response = urllib.request.urlopen(url=url)
                    data = response.read()
                    data = data.decode("gbk")
                    print( "新浪财经财务指标读取完毕!")
                    time.sleep(2)
                except Exception as e:
                    print(code, name, year, "年，新浪财经财务指标数据不存在！")
                    continue
                bs = bs4.BeautifulSoup(data,"lxml")
                table = bs.find('table',{'id':'BalanceSheetNewTable0'})
                tbody = table.find('tbody')
                rows = tbody.find_all('tr')
                Qt = 0
                for row in rows:
                    items = []
                    if row.find('strong') and row.find('strong').get_text()==u'报告日期':
                        Qt = len(row.findAll('td'))-1
                    elif findRow(row, u'摊薄每股收益(元)',items): epsavg = getData(items)
                    elif findRow(row, u'加权每股收益(元)', items): epsw = getData(items)
                    elif findRow(row, u'每股收益_调整后(元)', items): epsadj = getData(items)
                    elif findRow(row, u'扣除非经常性损益后的每股收益(元)', items): epsdiscount = getData(items)
                    elif findRow(row, u'每股净资产_调整前(元)', items): bvps_bfadj = getData(items)
                    elif findRow(row, u'每股净资产_调整后(元)', items): bvps_adj = getData(items)
                    elif findRow(row, u'每股经营性现金流(元)', items): epcf = getData(items)
                    elif findRow(row, u'每股资本公积金(元)', items): reservedps = getData(items)
                    elif findRow(row, u'每股未分配利润(元)', items): perundps = getData(items)
                    elif findRow(row, u'销售毛利率(%)', items): gpr = getData(items)
                    elif findRow(row, u'净资产收益率(%)', items): roe = getData(items)
                    elif findRow(row, u'加权净资产收益率(%)', items): roew = getData(items)
                    elif findRow(row, u'扣除非经常性损益后的净利润(元)', items):
                        net_profits_discount = [d/10**4 for d in getData(items)]
                    elif findRow(row, u'净利润增长率(%)', items): profits_yoy = getData(items)
                if bDataExit.count(False)>0:
                #将获取的数据插入数据表stock_report
                    for i in range(1,Qt+1):
                        if bDataExit[i-1]==False:#数据有缺失时，由前代码的逻辑必然数据表存在
                            sqlString = "insert into stockreport_"
                            sqlString += "%s" % (year)
                            sqlString += "_%s" % (i)
                            sqlString += "(code,name,eps,bvps,roe,net_profits,profits_yoy) values('"
                            sqlString += code
                            sqlString += "','"
                            sqlString += name
                            sqlString += "',"
                            sqlString += "%s" % (epsadj[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (bvps_adj[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (roe[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (net_profits_discount[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (profits_yoy[Qt-i])
                            sqlString += ")"
                            conn.execute(sqlString)
                            log.writeUtfLog(sqlString)
                            print("已增加", code, name, "数据至", year, "年",i, "季度，stockreport数据表")
                if bDataSupExist.count(False)>0:
                    for i in range(1,Qt+1):
                        if bDataSupExist[i-1]==False:#数据有缺失时，由前代码的逻辑必然数据表存在
                            sqlString = "insert into stockreport_sup_"
                            sqlString += "%s" % (year)
                            sqlString += "_%s" % (i)
                            sqlString += "(code,name,eps_avg,eps_w,eps_adj,eps_discount, bvps_bfadj,bvps_adj,"
                            sqlString += "epcf,reservedps,perundps,gpr,roe,roe_w,net_profits_discount) values('"
                            sqlString += code
                            sqlString += "','"
                            sqlString += name
                            sqlString += "',"
                            sqlString += "%s" % (epsavg[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (epsw[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (epsadj[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (epsdiscount[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (bvps_bfadj[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (bvps_adj[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (epcf[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (reservedps[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (perundps[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (gpr[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (roe[Qt-i])
                            sqlString += ","
                            sqlString += "%s" % (roew[Qt - i])
                            sqlString += ","
                            sqlString += "%s" % (net_profits_discount[Qt-i])
                            sqlString += ")"
                            conn.execute(sqlString)
                            log.writeUtfLog(sqlString)
                            print("已增加", code, name, "数据至", year, "年",i, "季度，stockreport_sup数据表")
    except Exception as e:
        print(e)
        exit(1)
    return True, startYear

def checkStockReport_BACKUP(code, startYear, endYear):
    """

    :rtype: object
    """

    def getData(body, idx, Quarter):
        databody = body.find_all('tr')[idx]
        dataList = []
        for i in range(1, Quarter):
            str = databody.find_all('td')[i].get_text()
            if str == '--':
                dataList.append(sG.sNINF)
            else:
                dataList.append(float(str))
        return dataList

    try:
        name, yearToMarket,_,_ = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print(code, name, yearToMarket,"年上市！")
        if yearToMarket>endYear:
            print(code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!")
            return False
        if yearToMarket>startYear:
            print(code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!")
            startYear = yearToMarket
        for year in range(startYear, endYear + 1):
            #bTableExit=[True, True, True, True] #数据库中stockreport业绩报表是否已存在，初始值为True存在
            bDataExit=[True, True, True, True] #stockreport业绩报表中的数据是否已存在，初始值为True存在
            #bTableSupExist = [True, True, True, True]#数据库中stockreport_sup业绩报表是否已存在，初始值为True存在
            bDataSupExist = [True, True, True, True]#stockreport_sup业绩报表中的数据是否已存在，初始值为True存在
            for Qt in range(1, 5):
                sqlString = "select code from stockreport_"
                sqlString += "%s" %(year)
                sqlString += "_%s " % (Qt)
                sqlString += "where code="
                sqlString += code
                conn = createDBConnection()
                try:
                    ret = conn.execute(sqlString)
                except Exception as e:
                    #bTableExit[Qt-1]=False
                    print(code, name, year, "年", Qt, "季度，stockreport数据表不存在！")
                    continue
                result = ret.first()
                if result is None:
                    bDataExit[Qt-1] = False
                    print(code, name, year, "年", Qt, "季度，stockreport数据表中无此股票！")
                else:
                    continue
            for Qt in range(1, 5):
                sqlString = "select code from stockreport_sup_"
                sqlString += "%s" %(year)
                sqlString += "_%s " % (Qt)
                sqlString += "where code="
                sqlString += code
                conn = createDBConnection()
                try:
                    ret = conn.execute(sqlString)
                except Exception as e:
                    #bTableSupExist[Qt-1]=False
                    print(code, name, year, "年", Qt, "季度，stockreport_sup数据表不存在！")
                    continue
                result = ret.first()
                if result is None:
                    bDataSupExist[Qt-1] = False
                    print(code, name, year, "年", Qt, "季度，stockreport_sup数据表中无此股票！")
                else:
                    continue
            if bDataExit.count(False)>0 or bDataSupExist.count(False)>0:
                url = "http://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/" #http://data.eastmoney.com/bbsj/yjbb/600887.html
                url += code
                url += "/ctrl/"
                url += "%s" %(year)
                url += "/displaytype/4.phtml"
                print("读取新浪财经财务指标......")
                data = urllib.urlopen(url).read()
                print("新浪财经财务指标读取完毕!")
                time.sleep(2)
                bs = bs4.BeautifulSoup(data,"lxml")
                body = bs.find('tbody')
                try:
                    datebody = body.find_all('tr')[0]
                except Exception as e:
                    print(code, name, year, "年", Qt, "季度，新浪财经年报数据不存在！")
                    continue
                year,month,day = splitDateString(datebody.find_all('td')[1].get_text())
                Qt = 5
                if month == 3: Qt = 2
                elif month == 6: Qt = 3
                elif month == 9: Qt = 4
                epsavg = getData(body, 2, Qt)
                epsw = getData(body, 3, Qt)
                epsadj = getData(body, 4, Qt)
                epsdiscount = getData(body, 5, Qt)
                bvps_bfadj = getData(body, 6, Qt)
                bvps_adj = getData(body, 7, Qt)
                epcf = getData(body, 8, Qt)
                reservedps = getData(body, 9, Qt)
                perundps = getData(body, 10, Qt)
                gpr = getData(body, 23, Qt)
                roe = getData(body, 30, Qt)
                roew = getData(body, 31, Qt)
                net_profits_discount = [d/10**4 for d in getData(body, 32, Qt)]
                profits_yoy = getData(body, 35, Qt)
                if bDataExit.count(False)>0:
                #将获取的数据插入数据表stock_report
                    for i in range(1,Qt):
                        if bDataExit[i-1]==False:#数据有缺失时，由前代码的逻辑必然数据表存在
                            sqlString = "insert into stockreport_"
                            sqlString += "%s" % (year)
                            sqlString += "_%s" % (i)
                            sqlString += "(code,name,eps,bvps,roe,net_profits,profits_yoy) values('"
                            sqlString += code
                            sqlString += "','"
                            sqlString += name
                            sqlString += "',"
                            sqlString += "%s" % (epsadj[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (bvps_adj[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (roe[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (net_profits_discount[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (profits_yoy[Qt-1-i])
                            sqlString += ")"
                            conn.execute(sqlString)
                            log.writeUtfLog(sqlString)
                            print("已增加", code, name, "数据至", year, "年",i, "季度，stockreport数据表")
                if bDataSupExist.count(False)>0:
                    for i in range(1,Qt):
                        if bDataSupExist[i-1]==False:#数据有缺失时，由前代码的逻辑必然数据表存在
                            sqlString = "insert into stockreport_sup_"
                            sqlString += "%s" % (year)
                            sqlString += "_%s" % (i)
                            sqlString += "(code,name,eps_avg,eps_w,eps_adj,eps_discount, bvps_bfadj,bvps_adj,"
                            sqlString += "epcf,reservedps,perundps,gpr,roe,roe_w,net_profits_discount) values('"
                            sqlString += code
                            sqlString += "','"
                            sqlString += name
                            sqlString += "',"
                            sqlString += "%s" % (epsavg[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (epsw[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (epsadj[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (epsdiscount[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (bvps_bfadj[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (bvps_adj[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (epcf[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (reservedps[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (perundps[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (gpr[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (roe[Qt-1-i])
                            sqlString += ","
                            sqlString += "%s" % (roew[Qt - 1 - i])
                            sqlString += ","
                            sqlString += "%s" % (net_profits_discount[Qt-1-i])
                            sqlString += ")"
                            conn.execute(sqlString)
                            log.writeUtfLog(sqlString)
                            print("已增加", code, name, "数据至", year, "年",i, "季度，stockreport_sup数据表")
    except Exception as e:
        print(e)
        exit(1)
    return True, startYear


def checkStockReportEastMoney(code, startYear, endYear):#EastMoney
    """

    :rtype: object
    """
    try:
        name, yearToMarket,_,_ = getStockBasics(code)
        if yearToMarket==0 : exit(1)
        print(code, name, yearToMarket,"年上市！")
        if yearToMarket>endYear:
            print(code, name, yearToMarket,"股票上市时间比结束查询时间晚，请重新输入查询结束时间!")
            return False
        if yearToMarket>startYear:
            print(code, name,"股票上市时间比起始查询时间晚,以上市年份为最早检查年份!")
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
                print(code, name, year, "年，stockreport数据库中无此股票！")
                bNeedWebData = True
            else:
                continue
            if bNeedWebData:
                if not bAccessWebData:
                    url = "http://data.eastmoney.com/bbsj/yjbb/" #http://data.eastmoney.com/bbsj/yjbb/600887.html
                    url += code
                    url += ".html"
                    print("读取东方财富年报数据......")
                    data = urllib.urlopen(url).read().decode("gbk")
                    bAccessWebData = True
                    print("东方财富年报数据读取完毕!")
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
                        sqlString += name
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
                        log.writeUtfLog(sqlString)
                        print( "已增加",code,name,"数据至",year,"年stockreport数据库")
                        break
    except Exception as e:
        print(e)
        exit(1)
    return True, startYear

def getStockBasics(code):
    try:
        sqlString = "select name, timetomarket from stockbasics "
        sqlString += "where code="
        sqlString += code
        conn = createDBConnection()
        ret = conn.execute(sqlString)
        result = ret.first()
    except Exception as e:
        print(e)
        exit(1)
    if result is None :
        print(code, "股票基本数据获取失败！")
        return "", 0
    elif result.timetomarket == 0:
        print(code, result.name,"股票上市时间数据为空！")
        return  result.name, 0
    y = int(result.timetomarket / 1E4)
    m = int( (result.timetomarket-y*1E4) / 1E2)
    d = int(result.timetomarket-y*1E4-m*1E2)
    return  result.name, y, m, d

def checkDistrib(code, startYear, endYear):
    try:
        date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        y,m,d = splitDateString(date)
        bAccessDataFinished = False
        for year in range(endYear, startYear-1, -1):
            table1 = "stockreport_"
            table1 += "%s_4" % (year)
            table2 = "stockreport_sup_"
            table2 += "%s_4" % (year)
            sqlString = "select "
            sqlString += table1
            sqlString += ".name,distrib,dividenTime from "
            sqlString += table1
            sqlString += " inner join "
            sqlString += table2
            sqlString += " on "
            sqlString += table1
            sqlString += ".code="
            sqlString += table2
            sqlString += ".code"
            sqlString += " where "
            sqlString += table1
            sqlString += ".code="
            sqlString += code
            try:
                conn = createDBConnection()
                ret = conn.execute(sqlString)
            except Exception as e:
                print(year,"年，分红数据访问出错！")
                print("checkDistrib（）：数据库访问错！")
                continue
            result = ret.first()
            if result is None:
                print(code, year, "年，stockreport表或stockreport_sup表中无此股票！")
                continue
            elif result.distrib is None or result.dividenTime is None:
                name = result.name
                print(code, name, year, "年，stockreport表分红数据为空或stockreport_sup表分红日期为空！")
                if bAccessDataFinished == False:
                    url = "http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/"
                    url += code
                    url += ".phtml"
                    print("读取新浪财经股票分红数据......")
                    response = urllib.request.urlopen(url=url)
                    data = response.read().decode("gbk")
                    print("新浪财经股票分红数据读取完毕！")
                    time.sleep(5)
                    bAccessDataFinished = True
                bs = bs4.BeautifulSoup(data, "lxml")
                table = bs.find('table',{'id':'sharebonus_1'})
                # div = bs.find("div")
                # table = div.find_all("table")[12]
                tbody = table.find("tbody")
                try:
                    tds = tbody.find_all("td")
                except Exception as e:
                    print(code, name, year, "年，新浪财经分红数据不存在！")
                    continue
                for i in range(0, len(tds)):
                    if(tds[i].string==u"实施"):
                        y,m,d = splitDateString(tds[i + 2].string)
                        if y<startYear: break
                        if year + 1 == y: # 网上的时间比实际分红时间要晚一年
                            sg = (tds[i - 3].string)
                            zg = (tds[i - 2].string)
                            px = (tds[i - 1].string)
                            dividenDate = (tds[i + 2].string)
                            if (u"0" != sg or u"0" != zg or u"0" != px):
                                sqlString = "update stockreport_"
                                sqlString += "%s" % (year)
                                sqlString += "_4 "
                                sqlString += "set "
                                sqlString += "distrib='10"
                                if px != u"0":
                                    sqlString += "派"
                                    sqlString += px
                                if zg != u"0":
                                    sqlString += "转"
                                    sqlString += zg
                                if sg != u"0":
                                    sqlString += "送"
                                    sqlString += sg
                                sqlString += "' where code="
                                sqlString += code
                                ret = conn.execute(sqlString)
                                log.writeUtfLog(sqlString)
                            if  dividenDate != '--':
                                sqlString = "update stockreport_sup_"
                                sqlString += "%s" % (year)
                                sqlString += "_4 "
                                sqlString += "set "
                                sqlString += "dividentime='"
                                sqlString += dividenDate
                                sqlString += "'"
                                sqlString += "where code="
                                sqlString += code
                                ret = conn.execute(sqlString)
                                log.writeUtfLog(sqlString)
                            print( year, "10派", px, "转", zg, "送", sg, "，", "分红登记日期：", dividenDate)
    except Exception as e:
        print(e)
        exit(1)
    return True

def splitDateString(date):
    if date:
        year = date[:4]
        month = date[5:7]
        day = date[8:]
        return int(year), int(month), int(day)
    else:
        return 0,0,0

def getDateString(year, month, day, short=False):
    date = "%s" % (year)
    date += "-"
    if month < 10:
        date += "0"
    date += "%s" % (month)
    date += "-"
    if day < 10:
        date += "0"
    date += "%s" % (day)
    if short: date = date.replace("-","")
    return date

def getFundPrice(code, dORy, month=0, day=0, autp=None):
    if month==0:#输入的日期在dORy中，以字符串形式输入
        y,m,d = splitDateString(dORy)
    else:
        y=dORy; m=month; d=day

    if createCalender().validDate(y,m,d):
        date = getDateString(y, m, d)
        conn = createDBConnection()
        sqlString = "select price from fundprice where code='"
        sqlString += code
        sqlString += "' and date='"
        sqlString += date
        sqlString += "'"
        try:
            ret = conn.execute(sqlString)
            result = ret.first()
        except Exception as e:
            print(e)
        if result is not None and result.price is not None:
            return True, result.price
        else:
            url = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=" + code
            url = url + "&page=1&per=20&sdate="
            url = url + date
            url = url + "&edate="
            url = url + date
            url = url + "&rt=0.19110643402290917"
            data = urllib.request.urlopen(url).read().decode("utf8")
            bs = bs4.BeautifulSoup(data, "html.parser")
            try:
                price = float(bs.find_all("td")[2].get_text())
                sqlString = "insert into fundprice(code,price,date) values('"
                sqlString += code
                sqlString += "',%s,'" % (price)
                sqlString += date
                sqlString += "')"
                try:
                    ret = conn.execute(sqlString)
                    log.writeUtfLog(sqlString)
                    return True, price
                except Exception as e:
                    print(e)
                    return False, 0
            except Exception as e:
                print(e)
                return False, 0
    else:
        return False, 0

def checkFundDistribSplit(code):
    #获取基金分红数据和基金份额拆分数据，用于计算份额变动
    url = "http://fundf10.eastmoney.com/fhsp_"
    url += code
    url += ".html"
    response = urllib.request.urlopen(url=url)
    data = response.read().decode("utf8")
    bs = bs4.BeautifulSoup(data, "lxml")
    # 获取基金分红数据
    tb = bs.find('table', {'class': 'w782 comm cfxq'})
    tbody = tb.find('tbody')
    rows = tbody.find_all('tr')
    distrib = []
    for row in rows:
        cells = row.find_all('td')
        if u"暂无分红信息" in cells[0].get_text(): break
        pos0 = cells[3].get_text().find(u'金')
        pos1 = cells[3].get_text().find(u'元')
        dis = float(cells[3].get_text()[pos0+1:pos1])
        distrib.append( (cells[1].get_text(), cells[2].get_text() , dis, cells[4].get_text()) )

    if distrib:
        #检查数据库中分红信息是否完整，不完整则填充
        sqlString = "select dateReg from funddistrib where code="
        sqlString += code
        try:
            conn = createDBConnection()
            ret = conn.execute(sqlString)
        except Exception as e:
            print(e)
            print("checkFundDistribSplit（）：funddistrib数据表访问错！")
            return
        result = ret.fetchall()
        if result:
            for d in distrib:
                try:
                    result.index((d[0],))
                except Exception as e:
                    sqlString = "insert into funddistrib"
                    sqlString += "(code,dateReg,dateDividen,dateBonus,bonus) values('"
                    sqlString += code
                    sqlString += "','"
                    sqlString += d[0]
                    sqlString += "','"
                    sqlString += d[1]
                    sqlString += "','"
                    sqlString += d[3]
                    sqlString += "',%s" % (d[2])
                    sqlString += ")"
                    try:
                        conn.execute(sqlString)
                        log.writeUtfLog(sqlString)
                    except Exception as e:
                        print(e)
                        print("checkFundDistribSplit(),基金分红信息插入失败")
        else:
            for d in distrib:
                sqlString = "insert into funddistrib"
                sqlString += "(code,dateReg,dateDividen,dateBonus,bonus) values('"
                sqlString += code
                sqlString += "','"
                sqlString += d[0]
                sqlString += "','"
                sqlString += d[1]
                sqlString += "','"
                sqlString += d[3]
                sqlString += "',%s" % (d[2])
                sqlString += ")"
                try:
                    conn.execute(sqlString)
                    log.writeUtfLog(sqlString)
                except Exception as e:
                    print(e)
                    print("checkFundDistribSplit(),基金分红信息插入失败")

    #获取基金份额拆分数据
    tb = bs.find('table', {'class': 'w782 comm fhxq'})
    tbody = tb.find('tbody')
    rows = tbody.find_all('tr')
    splitShare = []
    for row in rows:
        cells = row.find_all('td')
        if u"暂无拆分信息" in cells[0].get_text(): break
        ratio = cells[3].get_text().split(':')
        splitShare.append( (cells[1].get_text(), float(ratio[1])/float(ratio[0])) )

    if splitShare:
        #检查数据库中份额拆分数据是否完整，不完整则填充
        sqlString = "select splitdate from fundsharesplit where code="
        sqlString += code
        try:
            conn = createDBConnection()
            ret = conn.execute(sqlString)
        except Exception as e:
            print(e)
            print("checkFundDistribSplit（）：fundsharesplit数据表访问错！")
            return
        result = ret.fetchall()
        if result:
            for s in splitShare:
                try:
                    result.index((s[0],))
                except Exception as e:
                    sqlString = "insert into fundsharesplit"
                    sqlString += "(code,splitdate,ratio) values('"
                    sqlString += code
                    sqlString += "','"
                    sqlString += s[0]
                    sqlString += "','"
                    sqlString += s[1]
                    sqlString += ")"
                    try:
                        conn.execute(sqlString)
                        log.writeUtfLog(sqlString)
                    except Exception as e:
                        print(e)
                        print("checkFundDistribSplit(),基金拆分信息插入失败")
        else:
            for s in splitShare:
                sqlString = "insert into fundsharesplit"
                sqlString += "(code,splitdate,ratio) values('"
                sqlString += code
                sqlString += "','"
                sqlString += s[0]
                sqlString += "',"
                sqlString += '{}'.format(s[1])
                sqlString += ")"
                try:
                    conn.execute(sqlString)
                    log.writeUtfLog(sqlString)
                except Exception as e:
                    print(e)
                    print("checkFundDistribSplit(),基金拆分信息插入失败")

def getFundShareSplit(code):
    sqlString = "select splitdate, ratio from fundsharesplit where code="
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
    except Exception as e:
        print(e)
        print(code, "fundsharesplit数据表:访问失败！")
        return False, None
    result = ret.fetchall()
    if result:
        shareSplit = parseFundShareSplit(result)
        shareSplit.sort()
        return True, shareSplit
    else:
        print(code,"fundsharesplit数据表:分红数据获取失败,基金可能无分红！")
        return False, []

def parseFundShareSplit(s):
    shareSplit = []
    for e in s:
        shareSplit.append((e.splitdate, e.ratio))

    return shareSplit

def parseFundDistrib(d):
    distrib = []
    for dis in d:
        distrib.append((dis.dateDividen, dis.bonus, dis.dateBonus))

    return distrib

def getFundDistrib(code):
    sqlString = "select dateDividen,dateBonus,bonus from funddistrib where code="
    sqlString += code
    try:
        conn = createDBConnection()
        ret = conn.execute(sqlString)
    except Exception as e:
        print(e)
        print(code, "funddistrib数据表:访问失败！")
        return False, None
    result = ret.fetchall()
    if result:
        disturb = parseFundDistrib(result)
        disturb.sort()
        return True, disturb
    else:
        print(code,"funddistrib数据表:分红数据获取失败,基金可能无分红！")
        return False, []

def getMarketSign(code):
    c = code[0]
    if c in ("0","3"): return ".SZ"
    if c in ("6"): return ".SH"

def checkStockPrice(code, sDate, eDate):
    if sDate>eDate:
        print("checkStockPrice:查询时间有错！开始时间为 {},结束时间为 {}".format(sDate,eDate))
        return

    sDateTu, eDateTu = sDate.replace("-", ""), eDate.replace("-", "")

    conn = createDBConnection()
    sqlStringMin = "select min(date) as dateMin, max(date) as dateMax from stockprice where code={}".format(code)

    listPriceDF = []
    try:
        ret = conn.execute(sqlStringMin)
        r = ret.first()
        if r.dateMin:
            if sDate < r.dateMin:
                y, m, d = splitDateString(r.dateMin)
                y, m, d = createCalender().getPrevDay(y, m, d)
                date = getDateString(y, m, d, short=True)
                dfPriceMin = createTushare().daily(ts_code=code + getMarketSign(code), start_date=sDateTu, end_date=date)
                if not dfPriceMin.empty:
                    listPriceDF.append(dfPriceMin.loc[:, ['ts_code', 'close', 'trade_date']])
                else:
                    print("checkStockPrice:无法获取股票 {} 价格,开始时间为 {},结束时间为 {} 的价格信息！"\
                          .format(getStockNameByCode(code),sDateTu,date))
            if r.dateMax < eDate:
                y, m, d = splitDateString(r.dateMax)
                y, m, d = createCalender().getNextDay(y, m, d)
                date = getDateString(y, m, d, short=True)
                dfPriceMax = createTushare().daily(ts_code=code + getMarketSign(code), start_date=date, end_date=eDateTu)
                if not dfPriceMax.empty:
                    listPriceDF.append(dfPriceMax.loc[:, ['ts_code', 'close', 'trade_date']])
                else:
                    print("checkStockPrice:无法获取股票 {} 价格,开始时间为 {},结束时间为 {} 的价格信息！"\
                          .format(getStockNameByCode(code),date,eDateTu))
        else:#数据库没有任何该股票数据,向tushare获取数据
            dfPrice = createTushare().daily(ts_code=code + getMarketSign(code), start_date=sDateTu, end_date=eDateTu)
            if not dfPrice.empty:
                listPriceDF.append(dfPrice.loc[:,['ts_code', 'close', 'trade_date']])
            else:
                print("checkStockPrice:无法获取股票 {} 价格,开始时间为 {},结束时间为 {} 的价格信息！"\
                      .format(getStockNameByCode(code),sDateTu,eDateTu))
    except Exception as e:
        print(e)
        exit(1)

    if listPriceDF:
        dfPrice = pd.concat(listPriceDF)

        data=""
        for row in dfPrice.iterrows():
            data += "('{}',{},'{}-{}-{}'),".format(row[1][0][:-3],row[1][1],row[1][2][:4],row[1][2][4:6],row[1][2][6:])
        sqlString = "insert into stockprice(code,closeprice,date) values{}".format(data[:-1])
        try:
            conn.execute(sqlString)
            print(sqlString[:100]+"**********batch insert from tushare*********")
            log.writeUtfLog(sqlString[:100]+"**********batch insert from tushare*********")
        except Exception as e:
            print(e)
            print("checkStockPrice():股价信息插入失败！")







