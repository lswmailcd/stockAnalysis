#coding: utf-8

import matplotlib.pyplot as plt
import numpy as np
from pylab import mpl

n=2
dateDict = dict([(n-2,'20051230'), (n-1,'20071031'), (n,'20081231'),(n+1,'20140630'), (n+2,'20150529'), (n+3,'20160229'), (n+4,'20171222')])
colorDict = dict([(n-2,'r'), (n-1,'y'),(n,'c'),(n+1,'b'), (n+2,'r'), (n+3,'g'), (n+4,'k')])
u = dict([(n-2,31.3265259), (n-1,50.6886543),(n,29.53152814),(n+1,28.96705819), (n+2,43.84082492), (n+3,35.91712633), (n+4,32.80646143)])

wordGraph_Title=u"主板市场市盈率均值分析"
wordGraph_XLable = u'日期'
wordGraph_YLable = u'市盈率TTM'
xtickLable = []
xtick = []
ytick = []
for key in dateDict:
    xtickLable.append(dateDict[key])
    xtick.append(5*(key+1))
    ytick.append(u[key])
wordGraph_FontSize = 15
fig, ax = plt.subplots()
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
fs = wordGraph_FontSize
nyMax = np.max(ytick)
ylim = 10*(int(nyMax/10)+2)
ax.set_ylim(0,ylim)
yticklabel = np.zeros(ylim/10+2)
for i in range(ylim/10+2):
    yticklabel[i] = i*10
ax.set_ylabel(wordGraph_YLable, fontsize=fs)
ax.set_xlabel(wordGraph_XLable, fontsize=fs)
ax.set_title(wordGraph_Title, fontsize=fs)
rects1 = ax.bar(xtick, ytick, 3, color='c')
ax.set_xticks(xtick)
ax.set_xticklabels(xtickLable, fontsize=fs)
ax.set_yticklabels(yticklabel, fontsize=fs)
for key in dateDict:
    cr = colorDict[key]
    plt.hlines( ytick[key], 0, xtick[len(dateDict)-1], color=cr, label=dateDict[key] )
    print "date:", dateDict[key], "mean:", ytick[key]
plt.legend(loc='upper left')
plt.show()