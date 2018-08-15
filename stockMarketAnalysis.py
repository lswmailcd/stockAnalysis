# -*- coding: utf-8 -*-
import urllib
import numpy as np
import bs4
import xlrd
import xlwt
import tushare as ts
import time
import pandas as pd

#大智慧PE以第一至当前季度折算全年净利润进行计算
#TUSHARE的PE以第一至当前季度分季净利润加总折算全年PE,与大智慧PE数值较相似
#新浪财经计算的PE为TTM类型PE
#tushare的利润数据为摊薄后的利润

#读取market文件，确定当前证券的市场
market = xlrd.open_workbook('.\\data\\market.xlsx')
table = market.sheets()[0]
nMarketRows = table.nrows-1
a = np.zeros([nMarketRows])
marketCode = np.array(a, dtype=np.unicode)
marketName = np.array(a, dtype=np.unicode)
marketClass = np.array(a, dtype=np.unicode)
for i in range(nMarketRows):
    marketClass[i]= table.cell(i+1,0).value
    marketCode[i] = table.cell(i+1,1).value
    marketName[i] = table.cell(i+1,2).value

data = xlrd.open_workbook('.\\data\\data.xls')
table = data.sheets()[0]
nrows = table.nrows-1
a = np.zeros([nrows])
code = np.array(a, dtype=np.unicode)
name = np.array(a, dtype=np.unicode)
pe = np.array(a, dtype=np.unicode)
market = np.array(a, dtype=np.unicode)
idx = 0
for i in range(nrows):
    code[idx] = table.cell(i + 1, 0).value
    for j in range(nMarketRows):
        if code[idx] == marketCode[j]:
            market[idx] = marketClass[j]
            name[idx] = marketName[j]
            break
    idx += 1
workbook = xlwt.Workbook(encoding = 'ascii')
worksheet = workbook.add_sheet('stockBasic')
worksheet.write(0, 0, u"代码")
worksheet.write(0, 1, u"名称")
worksheet.write(0, 2, u"市盈率")
worksheet.write(0, 3, u"折扣率")
stockBasic = ts.get_stock_basics()
idx = 0
for i in range(nrows):
    for k in range(len(stockBasic)):
        if stockBasic.iloc[k:k+1].index[0]==code[i]:
            worksheet.write(i+1, 0, code[i])
            worksheet.write(i+1, 1, name[i])
            worksheet.write(i+1, 2, stockBasic.loc[code[i],'pe'])
            print code[i],name[i],stockBasic.loc[code[i],'pe']
            if stockBasic.loc[code[i],'pe']>1e-3:
                worksheet.write(i+1, 3, stockBasic.loc[code[i],'pe']*discountRate)
            break
#workbook.save('.\\data\\stockBasic.xls')

