import jdatetime

def timestamp_to_jalali(timestamp:str) -> str:
    timestamp = timestamp.replace('T',' ').replace('Z', '')
    splitted = timestamp.split(' ')
    date = list(map(int,splitted[0].split('-')))
    time = list(map(int,splitted[1].split(':')))

    return str(jdatetime.datetime.fromgregorian(day=date[2],month=date[1],year=date[0],hour=time[0],minute=time[1], second=time[2]))
