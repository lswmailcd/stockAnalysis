# coding:utf-8

from datetime import date

class stockCalender():
    def __init__(self):
        n=0

    def isLeapYear(self, y): #判断是否是闰年
        return y % 4 == 0 and y % 100 != 0 or y % 400 == 0

    def validDate(self, year, month, day):
        if day > 0:
            if (day < 32 and month in (1, 3, 5, 7, 8, 10, 12)) or (day < 31 and month in (2, 4, 6, 9, 11)) or (
                    month == 2 and day < (30 if self.isLeapYear(year) else 29) ):
                return True
        return False

    def getLastDay(self, y, m):
        if self.validDate(y, m, 15) == False:#1<=m<=12
            return -1

        if m in (1, 3, 5, 7, 8, 10, 12):
            return 31
        elif m in (4, 6, 9, 11):
            return 30
        else:
            if self.isLeapYear(y):
                return 29
            else:
                return 28

    def getQuarter(self, m ):
        if self.validDate(2000, m, 15) == False:#1<=m<=12
            return -1
        else:
            if m < 4:
                return 1
            elif m < 7:
                return 2
            elif m < 10:
                return 3
            else:
                return 4

    def getWeekday(self, y, m, d):
        return date(y, m, d).isoweekday() #1-星期一

    def getWorkdayForward(self, y, m, d):
        if m in (1,5) and d in(1,2,3) or m==10 and (d>0 and d<8):#五一，十一，元旦
            if m==1:
                m = 12
                y -=1
                d = 31
            else:
                m -= 1
                d = 30
        wd = self.getWeekday( y, m, d )
        if wd in (6,7):
            d1 = d - (wd-5)
            if self.validDate(y,m,d1):
                return y, m, d1
            else:
                m -= 1
                if self.validDate(y, m, 15):
                    d1 = self.getValidLastDay(y, m)
                    return self.getWorkdayForward(self, y, m, d1)
                else:
                    return self.getWorkdayForward(self, y-1, 12, self.getValidLastDay(y-1, 12))
        else:
            return y,m,d

    def getWorkdayBackward(self, y, m, d):
        if m in (1,5) and d in(1,2,3): d = 4 #五一，元旦
        if  m==10 and (d>0 and d<8): d = 8 #十一
        wd = self.getWeekday(y, m, d)
        if wd in (6,7):
            d1 = d + (8-wd)
            if self.validDate(y,m,d1):
                return y, m, d1
            else:
                m += 1
                if self.validDate(y, m, 15):
                    return self.getWorkdayBackward(self, y, m, 1)
                else:
                    return self.getWorkdayForward(self, y+1, 1, 1)
        else:
            return y,m,d

    def getPrevDay(self, y, m, d):#获得当前日期的前一天
        if d-1 == 0:
            if m-1 == 0:
                y -= 1
                m = 12
            else:
                m -= 1
            d = self.getLastDay(y, m)
        else:
            d -= 1
        return y, m, d

    def getNextDay(self, y, m, d):  # 获得当前日期的后一天
        if d+1 > self.getLastDay(y, m):
            if m+1 > 12 :
                y += 1
                m = 1
            else:
                m += 1
            d = 1
        else:
            d += 1
        return y, m, d

    def getPrevWorkday(self, y, m, d):#获得当前日期的前一个工作日
        y, m, d = self.getPrevDay(y, m, d)
        return self.getWorkdayForward(y, m, d)

    def getNextWorkday(self, y, m, d):#获得当前日期的后一个工作日
        y, m, d = self.getNextDay(y, m, d)
        return self.getWorkdayBackward(y, m, d)


