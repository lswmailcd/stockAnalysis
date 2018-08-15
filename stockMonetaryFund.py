# -*- coding: utf-8 -*-
import numpy as np
import xlrd

#统计货币基金的一年收益总和
data = xlrd.open_workbook('.\\data\\MF.xls')
table = data.sheets()[0]
nrows = table.nrows-1
idx = 5
InCome = 0.0
while idx < nrows:
    InCome += table.cell(idx, 0).value
    idx += 4
print "总收益为:", InCome