#!/usr/bin/python3
# coding=utf-8

import requests
import json
import datetime as dt
import pandas as pd
import numpy as np
import time
import os
import sys


class charts:
    def __init__(self):
        print("charts initialized")

    def time_array_converter(self, unix_time_stamp_array):
        time_stamp_array = []
        for a in unix_time_stamp_array:
            #print(a[0])
            x = dt.datetime.fromtimestamp(a[0])
            # print(x)
            time_stamp_array.append([x])

        return time_stamp_array

    def period_converter(self, period):
        if period=="1m" or period=="1M":
            period="60"
        elif period=="3m" or period=="3M":
            period="180"
        elif period=="15m" or period=="15M":
            period="900"
        elif period=="1h" or period=="1H":
            period="3600"
        elif period=="4h" or period=="4H":
            period="14400"
        elif period=="1d" or period=="1D":
            period="86400"
        elif period=="1w" or period=="1w":
            period="604800"
        else:
            period="0"
            raise Exception("Wrong period")

        return period

    def get_price_array_period(self, startTimestamp, endTimestamp, periods="4H", converter=True):
        periods=self.period_converter(periods)
        assert (startTimestamp < endTimestamp)
        query = {"periods": periods, "after": str(int(startTimestamp)), "before": str(int(endTimestamp))}
        res = \
        json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc", params=query).text)["result"][
            periods]
        res = np.array(res)
        time_stamp = res[:, 0].reshape(len(res), 1)

        if converter:
            time_stamp = self.time_array_converter(time_stamp)
        open_price = res[:, 1].reshape(len(res), 1)
        high_price = res[:, 2].reshape(len(res), 1)
        low_price = res[:, 3].reshape(len(res), 1)
        close_price = res[:, 4].reshape(len(res), 1)

        return (time_stamp, open_price, high_price, low_price, close_price)

    def save_chart_to_csv(self,time_stamp,open_price,high_price,low_price,close_price):
        all= np.c_[time_stamp,open_price, high_price,low_price,close_price]

        data = pd.DataFrame(all, columns={"time", "open", "high", "low", "close"})
        cwd = os.getcwd()
        data.to_csv(
            cwd + ".csv",
            index=False)

    def get_now_stamp(self):
        return int(dt.datetime.now().timestamp())

    def get_price_array_till_finaltime(self,final_unixtime_stamp=time.time(), num=100, periods="1m", converter=True):
        #print(periods)
        #print(int(self.period_converter(periods)))
        endTimestamp = final_unixtime_stamp
        startTimestamp = endTimestamp-int(self.period_converter(periods))*num
        (time_stamp, open_price, high_price, low_price, close_price)=\
            self.get_price_array_period(startTimestamp,endTimestamp, periods, converter)
        self.save_chart_to_csv(time_stamp, open_price, high_price, low_price, close_price)

        #print(np.shape(close_price))
        #print(close_price.T)
        #print(np.shape(close_price.T))

        return (time_stamp, open_price, high_price, low_price, close_price)

    def turn_vec_to_array(self,mat):
        #print(type(mat))

        b=[]
        for a in mat:
            b.append(a[0])

        return b

    def int_conv(self, array):

        for a in array:
            a=0

        return array

def int_conv( array):


    return array.astype(int)





if __name__ == '__main__':
    startDate = '2018-02-01 00:00:00'
    endDate = '2018-02-28 23:59:59'

    startDate = dt.datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    endDate = dt.datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')
    startTimestamp = startDate.timestamp()
    endTimestamp = endDate.timestamp()

    mycharts = charts()

    # now=mycharts.get_now_stamp()
    mycharts.get_price_array_till_finaltime()

    array=np.array([5.2,3.1])
    print(int_conv(array))

