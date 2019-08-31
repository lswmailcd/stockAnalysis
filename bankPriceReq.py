# -*- coding: utf-8 -*-
import urllib
import numpy as np
import re
import urllib2
import bs4
import stockGlobalSpace as sG
import stockTools as sT
import time
import json
import logRecoder as log

sqlString = "select * from bankproductbasics"
conn = sT.createDBConnection()
try:
    ret = conn.execute(sqlString)
except Exception, e:
    print  "连接bankproductbasics数据表失败！"
    exit(1)
product = ret.fetchall()

for p in product:
    url = "http://finance.ccb.com/cc_webtran/queryFinanceProdList.gsp?jsoncallback=jsonpCallback"
    textmod={"provinceId":"510","pageNo":1,"pageSize":12,"queryForm.saleStatus":"-1","queryForm.brand":"03"}
    textmod = urllib.urlencode(textmod)
    textmod += "&queryForm.name=" + p[0]
    textmod += "&queryForm.code=" + p[0]
    try:
        request = urllib2.Request(url=url, data=textmod,  headers=sG.browserHeaders) #data=textmod
        response = urllib2.urlopen(request)
        print
        print "获取" + p[0] + ":" + p[1] + "数据成功!"
        time.sleep(3)
    except Exception,e:
        print "获取"+p[0]+":"+p[1]+"数据失败!"
        continue
    data = response.read()
    bs = bs4.BeautifulSoup(data, "html.parser")
    jsonStr = bs.get_text().replace("\r","").replace("\n","")[14:-1]
    jsPair = json.loads(jsonStr)
    jsInfo = jsPair['ProdList'][0]
    if jsInfo['netval'] is None:
        print "获取"+p[0]+":"+p[1]+"当前净值数据失败!"
        continue
    dateStr = jsInfo['netvalDate']
    date = sT.getDateString(dateStr[:4],dateStr[4:6],dateStr[6:])

    sqlString = "select * from bankproductprice where "
    sqlString += "code='%s' and " % (p[0])
    sqlString += "date='%s'" % (date)
    try:
        ret = conn.execute(sqlString)
        result = ret.first()
        if result is not None:
            print date,p[1],":数据已经存在,无需更新！"
            continue
        else:
            sqlString = "insert into bankproductprice(code,price,date) values("
            sqlString += "'%s'," % (p[0])
            sqlString += "%s," % (jsInfo['netval'])
            sqlString += "'%s')" % (date)
            try:
                conn.execute(sqlString)
                log.writeUtfLog(sqlString)
                print sqlString
            except Exception, e:
                print p[0], " 更新数据表bankproductprice出错！"
                print e
                exit(1)
    except Exception, e:
        print p[0]," 数据表bankproductprice数据查找出错！"
        print e
        exit(1)
print "\n"
print "+"*10,"银行理财数据获取完毕！","+"*10

