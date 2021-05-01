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
import logRecoder as log

def subprocess(code, sYear, eYear):
    print("*******checking reports*******")
    try:
        sT.checkStockReport(code, sYear, eYear)
    except Exception as e:
        print(e)
    print("*******checking asset_debt*******")
    try:
        sT.checkStockAssetDebt(code, sYear, eYear)
    except Exception as e:
        print(e)
    print("*******checking distrib*******")
    try:
        sT.checkDistrib(code, sYear, eYear)
    except Exception as e:
        print(e)

def process(STARTYEAR, ENDYEAR, FileName):
    str = "*******************stockDataChecker开始检查......*******************"
    print(str)
    log.writeUtfLog(str)
    print("Checking year from", STARTYEAR, "to",ENDYEAR)
    print("Reading stock info from .\\data\\"+FileName)
    data = xlrd.open_workbook('.\\data\\'+FileName)
    print("Reading finished!")
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
            print(code[i], name[i])
            subprocess(code[i], STARTYEAR, ENDYEAR)
            sname, yearToMarket,_,_ = sT.getStockBasics(code[i])
            if yearToMarket == 0:
                print( code[i], name[i], u"上市时间不详!")
                exit(1)
            print("checking DONE!")

    str = "*******************stockDataChecker检查完成！*******************"
    print(str)
    log.writeUtfLog(str)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('ERROR: The cmd format is stockDataChecker.py startYear endYear')
        sys.exit(0)
    os.path.realpath(__file__)
    process(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])



