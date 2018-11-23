# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import stockTools as sT
#注意：此程序不要使用MYSQL数据进行查询，会使查询顺序无法控制！！！！！！！！！！
def getClosePrice(d):
    d=-1
    for i in range(6):
        d = ustr.find("\t",d+1)
    d1=ustr.find("\t",d+1)
    return ustr[d:d1]

#分月统计各类股票和基金的累积净值
date = time.strftime('%Y-%m-%d',time.localtime(time.time()))#"2018-05-31"#
y,m,d=sT.splitDateString(date)
#注意：此程序不要使用MYSQL数据进行查询股票的定义，会使查询股票顺序无法控制！！！！！！！！！！
data = xlrd.open_workbook('.\\data\\data.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
market = np.array(a, dtype=np.unicode)
count  = 0
for i in range(nrows):
    code[count] = table.cell(i + 1, 0).value
    name[count] = table.cell(i + 1, 1).value
    market[count] = table.cell(i + 1, 2).value
    count += 1
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('dataResult')
for i in range(count):
    foundData = 0
    if code[i] == u"" and name[i] == u"": continue
    if market[i]=="fund":
        dateToSearch = date
        while foundData == 0:
            url = "http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=" + code[i]
            url = url + "&page=1&per=20&sdate="
            url = url + dateToSearch
            url = url + "&edate="
            url = url + dateToSearch
            url = url + "&rt=0.19110643402290917"
            data = urllib.urlopen(url).read()
            bs = bs4.BeautifulSoup(data, "html.parser")
            foundData = 1
            try:
                closePrice = float(bs.find_all("td")[2].get_text())
            except Exception, e:
                print dateToSearch,code[i], name[i],u"没有今日数据!"
                y,m,d = sT.splitDateString(dateToSearch)
                dateToSearch = sT.getDateString(y,m,d-1)
                foundData=0
    elif market[i]!="fund":
        found,closePrice,actualDay = sT.getClosePriceForward( code[i],date )
        if found==True:
            foundData = 1
        else:
            print code[i], name[i], u"没有今日数据!"
            foundData = 0
    if foundData==1:
        print code[i], name[i], closePrice, sT.getDateString(y,m,actualDay)

    worksheet.write(i, 0, code[i])
    worksheet.write(i, 1, name[i])
    worksheet.write(i, 2, closePrice)
    worksheet.write(i, 3, sT.getDateString(y,m,actualDay))

#        url = "http://market.finance.sina.com.cn/downxls.php?date="
#        url += date
#        url += "&symbol="
#        url += market[i]
#        url += code[i]
#        data = urllib.urlopen(url).read()
#        ustr = data.decode('GBK')
#        print code[i], getClosePrice(ustr)
#        if not(u"当天没有数据" in ustr):
#            worksheet.write(i, 0, code[i])
#            worksheet.write(i, 1, float(getClosePrice(ustr)))
print u"查询证券价格的名义日期为:",date
workbook.save('.\\data\\dataResult.xls')