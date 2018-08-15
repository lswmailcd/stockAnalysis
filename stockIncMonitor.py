from sqlalchemy import create_engine

engine = create_engine('mysql://root:0609@127.0.0.1:3306/stockdatabase?charset=utf8', encoding='utf-8')
conn = engine.connect()
sqlString = "select * from stockBasics_20180126"
ret = conn.execute(sqlString)
nrow = ret.rowcount
data = ret.fetchall()
for i in range(nrow):
    sqlString = "select eps, net_profits from stockreport_2016_4 where code="
    sqlString += data[i].code
    ret = conn.execute(sqlString)
    try:
        if ret.rowcount!=0:
            data1 = ret.first()
            if data1.eps!=0:
                totals = data1.net_profits / data1.eps /1e4
                if  (data[i].totals - totals) > data[i].totals*0.1:
                    print data[i].code, data[i].name, totals, data[i].totals
    except Exception, e:
        print "error occur at ", data[i].code, data[i].name
