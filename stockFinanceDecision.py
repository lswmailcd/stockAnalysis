# -*- coding: utf-8 -*-

import numpy as np
import xlrd
import tushare as ts
import pandas as pd
from sqlalchemy import create_engine

ROEMIN = 20.0
COUNT = 3  #ROE和统计时间长度，以年为单位
GROSSRATEMIN = 30.0
NETRATEMIN = 5.0
MBRGMIN = 20.0
NPRGMIN = MBRGMIN
TIMETOMARKET = 20130101
YEARSTART = 2017  #毛利和净利增长的统计起始时间
YEAREND = 2018  #毛利和净利增长的统计结束时间，不包括该年

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
sqlString = "select * from stockbasics_20180126"
ret = conn.execute(sqlString)
nrow = ret.rowcount
data = ret.fetchall()
for i in range(nrow):
    code = data[i][0]
    name = data[i][1]
    timeToMarket = data[i][15]
    #ROE
    if timeToMarket < TIMETOMARKET:
        # 股东分成
        nROE=0
        for year in range(YEAREND-COUNT,YEAREND):
            sqlString = "select roe from stockreport_"
            sqlString += "%s" %(year)
            sqlString += "_4 where code="
            sqlString += code
            retROE = conn.execute(sqlString)
            if retROE.rowcount!=0 and retROE.first().roe>=ROEMIN:
                nROE=nROE+1
        if  nROE==COUNT:
            # 盈利能力:毛利率，净利率
            nGrossNet = 0
            for year in range(YEAREND-COUNT,YEAREND):
                sqlString = "select net_profit_ratio,gross_profit_rate from stockprofit_"
                sqlString += "%s" %(year)
                sqlString += "_4 where code="
                sqlString += code
                retGrossNetRate = conn.execute(sqlString)
                if retGrossNetRate.rowcount != 0:
                    grossNetRate = retGrossNetRate.first()
                    if grossNetRate.gross_profit_rate>= GROSSRATEMIN and grossNetRate.net_profit_ratio>=NETRATEMIN:
                        nGrossNet = nGrossNet + 1
            if nGrossNet==COUNT:
                #成长性：毛利增长率，净利增长率
                nMBNP=0
                for year in range(YEARSTART,YEAREND):
                    sqlString = "select mbrg,nprg from stockgrowth_"
                    sqlString += "%s" %(year)
                    sqlString += "_4 where code="
                    sqlString += data[i][0]
                    retMBNP = conn.execute(sqlString)
                    if retMBNP.rowcount != 0:
                        mbnp = retMBNP.first()
                        if mbnp.mbrg>= MBRGMIN and mbnp.nprg>=NPRGMIN:
                            nMBNP = nMBNP + 1
                if nMBNP==(YEAREND-YEARSTART): print code, name





