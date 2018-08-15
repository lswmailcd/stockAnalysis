# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import numpy as np
import matplotlib.pyplot as plt

peLowLimit = 0
peHighLimit = 100
n=0
#dateDict = dict([(n-1,'20071031'), (n,'20081231'),(n+1,'20140630'), (n+2,'20150529'), (n+3,'20160229'), (n+4,'20171222'), (n+5,'20180126'), (n+6,'20180619')])
#colorDict = dict([(n-1,'y'),(n,'c'),(n+1,'b'), (n+2,'r'), (n+3,'g'), (n+4,'k'), (n+5,'r'), (n+6,'k')])
dateDict = dict([(n,'20081231'),(n+1,'20140630'), (n+2,'20111230'), (n+3,'20171222'), (n+4,'20180126'), (n+5,'20180619'), (n+6,'20180803')])
colorDict = dict([(n,'b'),(n+1,'g'),  (n+2,'c'), (n+3,'k'), (n+4,'y'), (n+5,'r'), (n+6,'r')])

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
data = conn.execute("select code,name,stocktype from stockindex where stocktype='sh_main' \
                    or stocktype='sz_main'").fetchall()
nrow  = len(data)
peList = [[0]*nrow for key in dateDict]
profitList = [[0]*nrow for key in dateDict]
stockNumList = [[0]*len(dateDict)]
foundList = [[False]*nrow for key in dateDict]
stockIdxList = [[False]*nrow]
for key in dateDict:
    for i in range(nrow):
        sqlString = "select pe, profit_dynamic from pe_main_"
        sqlString += dateDict[key]
        sqlString += " where code="
        sqlString += data[i][0]
        ret = conn.execute(sqlString)
        if(ret.rowcount!=0):
            result = ret.first()
            pe = result.pe
            profit = result.profit_dynamic
            if pe < peLowLimit or pe > peHighLimit:
                continue
            foundList[key][i] = True
            peList[key][i] = pe
            profitList[key][i] = profit
            stockNumList[0][key] += 1
stockValidNum = 0
for j in range(nrow):
    found = True
    for key in dateDict:
        if foundList[key][j] == False:
            found = False
            break;
    if found == True:
        stockValidNum += 1
        stockIdxList[0][j] = True
peValidList = [[0] * stockValidNum for key in dateDict]
profitValidList = [[0] * stockValidNum for key in dateDict]
idx = 0
for j in range(nrow):
    if stockIdxList[0][j] == True:
        for key in dateDict:
            peValidList[key][idx] = peList[key][j]
            profitValidList[key][idx] = profitList[key][j]
        idx += 1
for key in dateDict:
    avgProfit = np.mean(profitValidList[key])
    medProfit = np.median(profitValidList[key])
    u = np.mean(peValidList[key])
    sig = np.std(peValidList[key])
    med = np.median(peValidList[key])
    print "date:", dateDict[key], "stockNum:", stockValidNum, "mean:", u, "median:", med, "std:", sig, "mProfit:", avgProfit, "medProfit:", medProfit
    x = np.linspace(u - 3*sig, u + 3*sig, 50)
    y_sig = np.exp(-(x - u) ** 2 /(2* sig **2))/(np.math.sqrt(2*np.math.pi)*sig)
    cr = colorDict[key]
    cr += "-"
    plt.plot(x, y_sig, cr,linewidth=2, label=dateDict[key])
    plt.plot([u,u],[0,0.02], cr);
    cr = colorDict[key]
    cr += "+"
    plt.plot([med, med], [0, 0.02], cr)
plt.legend(loc='upper left')
plt.title('stockPEDecision')
plt.show()
