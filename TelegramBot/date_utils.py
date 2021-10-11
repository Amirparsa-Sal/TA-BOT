import jdatetime
from datetime import datetime


def timestamp_to_jalali(timestamp:str) -> str:
    timestamp = timestamp.replace('T',' ').replace('Z', '')
    splitted = timestamp.split(' ')
    date = list(map(int,splitted[0].split('-')))
    time = list(map(int,splitted[1].split(':')))

    return str(jdatetime.datetime.fromgregorian(day=date[2],month=date[1],year=date[0],hour=time[0],minute=time[1], second=time[2]))

def jalali_to_gregorian(timestamp:str) -> str:
    splitted = timestamp.split(' ')
    date = list(map(int,splitted[0].split('-')))
    time = list(map(int,splitted[1].split(':')))

    return str(jdatetime.datetime(day=date[2],month=date[1],year=date[0],hour=time[0],minute=time[1], second=time[2]).togregorian())
    
def is_valid_date_time(timestamp:str) -> bool:
    try:
        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False
    else:
        return True