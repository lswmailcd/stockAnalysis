#coding:utf8

import threading
#定义所有的全局变量
bConnBD=False
dbConnection = None
engine = None
Calender = None
sINF = 10**10
sNINF = -sINF
lock = threading.Lock()
