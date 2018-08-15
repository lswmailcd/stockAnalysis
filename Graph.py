#coding:utf-8

import numpy as np
import matplotlib.pyplot as plt
from pylab import mpl

def  drawColumnChat( ax, XList, YList, title, xLableName, yLableName, fontSize, barWidth, bIntDisp=False ):
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
    mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
    fs = fontSize
    nMaxY = np.max(YList)
    if nMaxY<50:scale=10
    elif nMaxY<100: scale=20
    elif nMaxY<300: scale = 50
    else:scale = 100
    ylim = scale*(int(nMaxY/scale)+2)
    ax.set_ylim(0,ylim)
    yticklabel = np.zeros(10)
    for i in range(10):
        yticklabel[i] = i*scale
    ax.set_ylabel(yLableName, fontsize=fs)
    ax.set_xlabel(xLableName, fontsize=fs)
    ax.set_title(title, fontsize=fs)
    rects1 = ax.bar(XList,YList, barWidth, color='b')
    autolabel(rects1, ax, fontSize,bIntDisp)
    ax.set_xticks(XList)
    ax.set_xticklabels(XList, fontsize=fs)
    ax.set_yticklabels(yticklabel, fontsize=fs)
    return

def autolabel(rects, ax, fs, bIntDisp):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        if bIntDisp:
            h = str(int(round(height,1)))
        else:
            h = str(round(height,2))
        ax.text(rect.get_x() + rect.get_width()/2., 1.01*height,h,ha='center', va='bottom', fontsize=fs)
    return