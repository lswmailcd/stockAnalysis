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

def subprocess(code, sYear, eYear, bOptCheck=False):
    print('*'*10+'checking START'+'*'*10)
    #alway check when called, must check before checkStockFinanceReport()
    sT.checkStockPrice(code, sT.getDateString(sYear, 1, 1), sT.getDateString(eYear, 12, 31))
    sT.checkStockShare(code)

    if bOptCheck:
        print("*******checking financial reports*******")
        try:
            sT.checkStockFinanceReport(code, sYear, eYear)
        except Exception as e:
            print(e)
        print("*******checking asset&debt reports*******")
        try:
            sT.checkStockAssetDebt(code, sYear, eYear)
        except Exception as e:
            print(e)
        print("*******checking distrib reports*******")
        try:
            sT.checkDistrib(code, sYear, eYear)
        except Exception as e:
            print(e)



    print('*'*10+'checking DONE'+'*'*10)

def process(STARTYEAR, ENDYEAR, FileName):
    s = "\n*******************stockDataChecker开始检查......*******************\n"
    print(s)
    print("Checking year from", STARTYEAR, "to",ENDYEAR)
    print("Reading stock info from .\\data\\"+FileName)
    data = xlrd.open_workbook('.\\data\\'+FileName)
    print("Reading finished!")
    table = data.sheets()[0]
    nrows = table.nrows-1
    a = np.zeros([nrows])
    code = np.array(a, dtype=np.compat.unicode)
    name = np.array(a, dtype=np.compat.unicode)
    for i in range(nrows):
        if table.cell(i + 1, 0).value!="":
            code[i] = table.cell(i + 1, 0).value
            if code[i] == "" or code[i]=='0.0': continue
            name[i] = sT.getStockNameByCode(code[i])
            print(code[i], name[i])
            subprocess(code[i], STARTYEAR, ENDYEAR)
            sname, yearToMarket,_,_ = sT.getStockBasics(code[i])
            if yearToMarket == 0:
                print( code[i], name[i], u"上市时间不详!")
                exit(1)
            print("checking DONE!")

    s = "\n*******************stockDataChecker检查完成！*******************\n"
    print(s)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('ERROR: The cmd format is stockDataChecker.py startYear endYear')
        sys.exit(0)
    os.path.realpath(__file__)
    process(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])



