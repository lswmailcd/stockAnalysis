# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import numpy as np
import matplotlib.pyplot as plt
import Graph

peLowLimit = 0
peHighLimit = 100
n=-2
#dateDict = dict([(n-1,'20071031'), (n,'20081231'),(n+1,'20140630'), (n+2,'20150529'), (n+3,'20160229'), (n+4,'20171222'), (n+5,'20180126'), (n+6,'20180619')])
#colorDict = dict([(n-1,'y'),(n,'c'),(n+1,'b'), (n+2,'r'), (n+3,'g'), (n+4,'k'), (n+5,'r'), (n+6,'k')])
dateDict = dict([(n+2,'20051230'),(n+3,'20081031'),(n+4,'20121130'), (n+5,'20140130'),(n+6,'20160229'), \
                 (n+7,'20181228'), (n+8,'20190131'), (n+9,'20190301'), \
                 (n+10, '20180131'),(n+11, '20150529'),(n+12, '20090731'),(n+13, '20071031') ])
#colorDict = dict([(n,'b'),(n+1,'g'),  (n+2,'c'), (n+3,'k'), (n+4,'y'), (n+5,'b'), (n+6,'r'), (n+7,'k'), (n+8,'k'), (n+9,'k')])

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
data = conn.execute("select code,name from stockbasics where code like '600%%'\
                     or code like '601%%' or code like '000%%' or code like '001%%'").fetchall()
nrow  = len(data)
codeList = [[0]*nrow for key in dateDict]
nameList = [[0]*nrow for key in dateDict]
peList = [[0]*nrow for key in dateDict]
profitList = [[0]*nrow for key in dateDict]
stockNumList = [[0]*len(dateDict)]
foundList = [[False]*nrow for key in dateDict]
stockIdxList = [[False]*nrow]
for key in dateDict:
    for i in range(nrow):
        sqlString = "select code, name, pe, profit_dynamic from pe_main_"
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
            codeList[key][i] = result.code
            nameList[key][i] = result.name
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
codeValidList = [[0] * stockValidNum for key in dateDict]
nameValidList = [[0] * stockValidNum for key in dateDict]
peValidList = [[0] * stockValidNum for key in dateDict]
profitValidList = [[0] * stockValidNum for key in dateDict]
idx = 0
for j in range(nrow):
    if stockIdxList[0][j] == True:
        for key in dateDict:
            codeValidList[key][idx] = codeList[key][j]
            nameValidList[key][idx] = nameList[key][j]
            peValidList[key][idx] = peList[key][j]
            profitValidList[key][idx] = profitList[key][j]
        idx += 1
for i in range(0,idx):
    print codeValidList[0][i], nameValidList[0][i]

dateList=[]
peMeanList=[]
peMedianList=[]
for key in dateDict:
    dateList.append(dateDict[key])
    u = np.mean(peValidList[key])
    sig = np.std(peValidList[key])
    med = np.median(peValidList[key])
    peMeanList.append(u)
    peMedianList.append(med)
    avgProfit = np.mean(profitValidList[key])
    medProfit = np.median(profitValidList[key])
    print "date:", dateDict[key], "stockNum:", stockValidNum, "mean:", u, "median:", med, "std:", sig, "mProfit:", avgProfit, "medProfit:", medProfit

fig = plt.figure()
ax1 = fig.add_subplot(2,1,1,xlim=(-1, len(dateList)), ylim=(-4, 4))
ax2 = fig.add_subplot(2,1,2,xlim=(-1, len(dateList)), ylim=(-4, 4))
#ax3 = fig.add_subplot(3,1,3,xlim=(YEARSTART-1, YEAREND+1), ylim=(-4, 4))
Graph.drawColumnChat( ax1, dateList, peMeanList, u'市场PE历史图(各时期股票相同)', u'', u'PE mean', 12, 0.5)
Graph.drawColumnChat( ax2, dateList, peMedianList, u'', u'', u'PE median', 12, 0.5)
#Graph.drawColumnChat( ax3, YEARList, PBList, u'', u'', u'PB', 20, 0.5)
print u"市场PE历史图绘制完成"
plt.show()

# for key in dateDict:
#     avgProfit = np.mean(profitValidList[key])
#     medProfit = np.median(profitValidList[key])
#     u = np.mean(peValidList[key])
#     sig = np.std(peValidList[key])
#     med = np.median(peValidList[key])
#     print "date:", dateDict[key], "stockNum:", stockValidNum, "mean:", u, "median:", med, "std:", sig, "mProfit:", avgProfit, "medProfit:", medProfit
#     x = np.linspace(u - 3*sig, u + 3*sig, 50)
#     y_sig = np.exp(-(x - u) ** 2 /(2* sig **2))/(np.math.sqrt(2*np.math.pi)*sig)
#     cr = colorDict[key]
#     cr += "-"
#     plt.plot(x, y_sig, cr,linewidth=2, label=dateDict[key])
#     plt.plot([u,u],[0,0.02], cr);
#     cr = colorDict[key]
#     cr += "+"
#     plt.plot([med, med], [0, 0.02], cr)
# plt.legend(loc='upper left')
# plt.title('stockPEDecision')
# plt.show()
