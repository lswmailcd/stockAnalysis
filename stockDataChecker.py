#coding:utf-8

import sys
import os
from sqlalchemy import create_engine
import numpy as np
import urllib
import bs4
import time
import xlrd
import xlwt
import stockTools as sT

def process(STARTYEAR, ENDYEAR, FileName):
    print "*******************stockDataChecker开始检查......*******************"
    print "Checking year from", STARTYEAR, "to",ENDYEAR
    print "Reading stock info from .\\data\\"+FileName
    data = xlrd.open_workbook('.\\data\\'+FileName)
    print "Reading finished!"
    table = data.sheets()[0]
    nrows = table.nrows-1
    a = np.zeros([nrows])
    code = np.array(a, dtype=np.unicode)
    name = np.array(a, dtype=np.unicode)
    for i in range(nrows):
        if table.cell(i + 1, 0).value!="":
            code[i] = table.cell(i + 1, 0).value
            if code[i] == "" or code[i]=='0.0': continue
            name[i] = sT.getStockNameByCode(code[i]).decode('utf8')
            print code[i], name[i]
            print "checking reports..."
            found, STARTYEAR = sT.checkStockReport(code[i], STARTYEAR, ENDYEAR)
            if found == False: exit(1)
            print "checking distrib..."
            if sT.checkDistrib(code[i], STARTYEAR, ENDYEAR) == False: exit(1)
            sname, yearToMarket = sT.getStockBasics(code[i])
            if yearToMarket == 0:
                print code[i], name[i], u"上市时间不详!"
                exit(1)
            print "checking DONE!"

    print "*******************stockDataChecker检查完成！*******************"

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'ERROR: The cmd format is stockDataChecker.py startYear endYear'
        sys.exit(0)
    os.path.realpath(__file__)
    process(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])



