#coding:utf8

import threading
#定义所有的全局变量
bConnBD=False
dbConnection = None
engine = None
Calender = None
Tushare = None
sINF = 10**10
sNINF = -sINF
epsilon = 0.00001
lock = threading.Lock()
browserHeaders = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}


