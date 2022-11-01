import datetime
#from pytz import timezone

def now():
    dt = datetime.datetime.utcnow()
    td = datetime.timedelta(hours=9)
    jst_now = dt + td
    #t_delta = datetime.timedelta(hours=9)
    #JST = datetime.timezone(t_delta, 'JST')
    #jst_now = datetime.datetime.now(JST)
    return jst_now
