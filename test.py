import datetime as dt
x = dt.datetime.now
dt.strptime(x,"%d%b%Y%H%M%S")
print(x.time())
