#!/usr/bin/python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.finance as mpf
from matplotlib.dates import date2num
import time



def plot_candles(time_stamp, price):
    print("plot_candles")

    time_start=time_stamp[0]

    length=len(time_stamp)
    print(length)
    time_end = time_stamp[length-1]

    # print(time_stamp)

    print(str(time_start[0]))
    print(str(time_end[0]))


    idx = pd.date_range(str(time_start[0]), str(time_end[0]), freq='H')
    # print(type(price.T))
    # print(np.shape(price.T))
    print(idx)

    # new_price=np.reshape(price.T, (201,))
    # print(new_price)

    df = pd.Series(price.T[0], index=idx).resample('B').ohlc()
    fig = plt.figure()
    ax = plt.subplot()

    xdate = [x.date() for x in df.index]  # Timestamp -> datetime

    # print(xdate)
    ohlc = np.vstack((date2num(xdate), df.values.T)).T  # datetime -> float
    print(df.values)
    mpf.candlestick_ohlc(ax, ohlc, width=0.1, colorup='g', colordown='r')
    ax.grid()  # グリッド表示
    ax.set_xlim(df.index[0].date(), df.index[-1].date())  # x軸の範囲
    fig.autofmt_xdate()  # x軸のオートフォーマット

    fig.show()

    time.sleep(20)




#########################
if __name__ == '__main__':

    idx = pd.date_range('2015/01/01 00:00', '2015/12/31 23:59', freq='T')
    dn = np.random.randint(2, size=len(idx))*2-1
    rnd_walk = np.cumprod(np.exp(dn*0.0002))*100
    print(np.shape(rnd_walk))
    print(type(rnd_walk))
    print(idx)

    df = pd.Series(rnd_walk, index=idx).resample('B').ohlc()


    # df.plot()

    fig = plt.figure()
    ax = plt.subplot()

    xdate = [x.date() for x in df.index] #Timestamp -> datetime

    # print(xdate)
    ohlc = np.vstack((date2num(xdate), df.values.T)).T #datetime -> float
    # print(df.values)
    mpf.candlestick_ohlc(ax, ohlc, width=0.7, colorup='g', colordown='r')
    ax.grid() #グリッド表示
    ax.set_xlim(df.index[0].date(), df.index[-1].date()) #x軸の範囲
    fig.autofmt_xdate() #x軸のオートフォーマット

    fig.show()


    time.sleep(3)
