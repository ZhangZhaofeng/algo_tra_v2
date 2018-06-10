
import pandas as pd
import numpy as np
import time

def data2csv(datas, csvname = 'log_csv.csv'):

    # datas is a array
    all = [datas]
    data = pd.DataFrame(all)
    data.to_csv('log_csv.csv', mode='a', header=False)

if __name__ == '__main__':
    amount = 0.13
    trigger = 100000
    datas = [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_STOP',  '%f'%(amount), '%f'%(trigger)]
    data2csv(datas)