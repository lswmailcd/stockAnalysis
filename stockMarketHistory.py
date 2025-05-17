import stockTools as sT
import matplotlib.pyplot as plt
import Graph
import pandas as pd
import mplfinance as mpf
from pylab import mpl

#起始年月
startDate=sT.getDateString(2025,1,1)
#结束年月
endDate=sT.getCurrentDate()
#endDate=sT.getDateString(2024,3,16)

str = input("如不需要获取指数信息请按回车，如需获取请按'c': ")
if str=="c":
    sT.checkStockIndex('sh000001')
    sT.checkStockIndex('sz399001')



datalist=[]
startDate = startDate if sT.isWorkday(startDate) else sT.getNextWorkday(startDate)
endDate = endDate if sT.isWorkday(endDate) else sT.getPrevWorkday(endDate)
date=startDate
datalist.append(date)
while date<endDate:
    date = sT.getNextWorkday(date)
    datalist.append(date)

indexList=[]
sT.getStockIndexList('000001',indexList,startDate,endDate)

amountlist=[]
for date in datalist:
    amountSH = sT.getStockIndexAmount('000001',date)
    amountSZ = sT.getStockIndexAmount('399001',date)
    amountlist.append((date, (amountSH+amountSZ)/1e8))


def getAxesInfo( datalist, xlist, ylist, xticklist ):
    xlist.clear(); ylist.clear(); xticklist.clear()
    for i, x in enumerate(datalist, 1):
        xlist.append(i)
        ylist.append(x[1])
        xticklist.append(x[0])

xlist, ylist, xticklist = [],[],[]
fig = plt.figure()
fig.canvas.manager.set_window_title("情绪指数-沪深成交金额")

nRows = 2
ax = []
for i in range(0,nRows):
    ax.append(plt.subplot2grid((nRows, 1), (i, 0)))

fs = 10
fmtXlimit = 10

j=0
ax[0].set_title('上证指数', fontsize=fs)
ax00 = ax[0]
ax01 = ax[0].twinx()

indexList = [ [d, o, c, h, l] for o, c, h, l, _, d in indexList]
dfIndex = pd.DataFrame(indexList)
dfIndex.columns = ['Date','Open','Close','High','Low']
dfIndex.set_index(['Date'],inplace=True)
dfIndex.index = pd.DatetimeIndex(dfIndex.index)
# 调用make_marketcolors函数，定义K线颜色
mc = mpf.make_marketcolors(
    up="red",  # 上涨K线的颜色
    down="aquamarine",  # 下跌K线的颜色
    edge="black",  # 蜡烛图箱体的颜色
    volume="blue",  # 成交量柱子的颜色
    wick="black"  # 蜡烛图影线的颜色
)
style = mpf.make_mpf_style(base_mpl_style="ggplot", marketcolors=mc)
mpf.plot(dfIndex, ax=ax00, type='candle', xrotation=15, datetime_format='%Y-%m-%d', volume=False, show_nontrading=False, style=style)
ax[0].xaxis.set_major_locator(mpl.ticker.MultipleLocator(3))
Graph.my_autofmt_xdate(ax[0])
ax[0].grid(True)

j+=1
getAxesInfo( amountlist, xlist, ylist, xticklist )
Graph.drawColumnChat( ax[j], xlist, ylist, xticklist, ylist, '沪深股市总成交额（亿元)', u'', u'',\
                      fs, 0.5, bfmtX=True if len(xticklist)>fmtXlimit else False, barcolor='lightskyblue')
ax[j].axhline(color='cornflowerblue',y=ylist[-1])
ax[j].xaxis.set_major_locator(mpl.ticker.MultipleLocator(3))
Graph.my_autofmt_xdate(ax[j])

print("市场成交额图绘制完成！")
plt.show()
