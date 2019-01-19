# coding:utf-8

import time

def writeUtfLog(txt):
    f = open('./data/logFile.txt','a')
    f.write('\n')
    strLog = time.strftime('%Y-%m-%d,%H:%M:%S',time.localtime(time.time()))
    strLog +=':  '
    strLog += txt
    f.write( strLog )
    f.write('\n')
    f.close