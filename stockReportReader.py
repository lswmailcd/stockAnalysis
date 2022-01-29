import numpy as np
import urllib
import bs4
import xlrd
import stockTools as sT
import time
from random import randint

startdate = time.strftime('%Y-%m-%d',time.localtime(time.time()-24*60*60*90))#公告起始时间为三个月前
endate = time.strftime('%Y-%m-%d',time.localtime(time.time()))

data = xlrd.open_workbook('.\\data\\StockList.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.compat.unicode)
name = np.array(a, dtype=np.compat.unicode)
count = 0
for i in range(nrows):
    if table.cell(i + 1, 0).value!="":
        code[count] = table.cell(i + 1, 0).value
        name[count] = sT.getStockNameByCode(code[count])
        sname, yearToMarket,_,_ = sT.getStockBasics(code[count])
        if yearToMarket == 0:
            print( code[count], name[count], u"上市时间不详!")
            exit(1)
        count += 1
            
for i in range(count):
    time.sleep(randint(1,3))
    url = "https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllBulletin/stockid/"
    url += code[i]
    url += ".phtml"
    response = urllib.request.urlopen(url=url)
    # response = urllib.urlopen(request)
    data = response.read().decode("gbk")
    bs = bs4.BeautifulSoup(data, "lxml")
    table = bs.find_all('table',{'class':'table2'})[1]
    div = table.find('div',{'class':'datelist'})
    tlist = div.get_text().split()
    noticeList=[]
    for j in range(len(tlist)-1):
        if j<len(tlist)-2:
            noticeList.append((tlist[j][-10:], tlist[j+1][:-10]))
        else:
            noticeList.append((tlist[j][-10:], tlist[j+1]))

    for d, c in noticeList:
        if startdate<=d<=endate and "回购" in c:
            print(d,c)
    print()

