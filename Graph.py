#coding:utf-8

import numpy as np
import matplotlib.pyplot as plt
from pylab import mpl
import win32api,win32con

width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)   #获得屏幕分辨率X轴
height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)   #获得屏幕分辨率Y轴


def  drawColumnChat( ax, XList, YList, XtickLableList, YtickLableList, title, xLableName, yLableName, \
                     fontSize, barWidth, bIntDisp=False, bPercent=False ):
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
    mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
    fs = fontSize

    ax.set_title(title, fontsize=fs)
    ax.set_xlabel(xLableName, fontsize=fs)
    ax.set_ylabel(yLableName, fontsize=fs)
    if XList is not None: ax.set_xticks(XList)
    ax.set_xticklabels(XtickLableList, fontsize=fs)
    ax.axhline(color='black')
    if XList is not None:
        rects1 = ax.bar(XList,YList, barWidth, color='b')
    else:
        rects1 = ax.bar(XtickLableList, YList, barWidth, color='b')
    autolabel(rects1, ax, fontSize,bIntDisp,bPercent)
    for ax in plt.gcf().axes:
        for yticklabel in ax.get_yticklabels():
            yticklabel.set_fontsize(fs)
    return

def autolabel(rects, ax, fs, bIntDisp, bPercent):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        n = height
        if bPercent: n=n*100.0
        if bIntDisp:
            h = str(int(round(n,0)))
        else:
            h = str(round(n,2))
        if bPercent: h = h + '$\%$'
        if height<0: height = 0
        ax.text(rect.get_x() + rect.get_width() / 2., height, h, ha='center', va='bottom', fontsize=fs)

def  drawRateChat( XList, YList, labelList, title, saveImg=False, dir="" ):
    plt.figure(figsize=((width-10) / 100.0, (height-10) / 100.0))
    yScaleMaxList,yScaleMinList=[],[]
    for yList,name in zip(YList, labelList):  # 日期选择一个日期，坐标轴不能有两种不同的日期表示
        yList = [y*100.0 for y in yList]
        yScaleMaxList.append(max(yList))
        yScaleMinList.append(min(yList))
        plt.plot(XList, yList, label=name)
    ax = plt.gca()
    ax.set_title(title, fontsize=20)
    minY, maxY = min(yScaleMinList), max(yScaleMaxList)
    yScale = 5 if (maxY - minY)<300.0 else 10
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(yScale))
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f%%"))
    ax.axhline(color='black', y=0)
    ax.axhline(color='red', y=12.5)
    ax.axhline(color='red', y=60)
    ax.axhline(color='red', y=100)
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
    plt.legend(loc=0, ncol=6, mode="expand", borderaxespad=0.0)
    plt.gcf().autofmt_xdate()
    plt.grid(True)
    if saveImg: plt.savefig(dir)
    plt.show()