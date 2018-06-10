#!/usr/bin/python3
# coding=utf-8

import datetime
import pandas
import seaborn
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ohlc as plot_candle
from oandapyV20 import API
import oandapyV20.endpoints.instruments as oandapy

if __name__ == '__main__':
    now          = datetime.datetime.now() - datetime.timedelta(hours = 9) # 標準時に合わせる
    minutes      = 61 # 60分取得
    time_min     = now - datetime.timedelta(minutes = 120) # 2時間前からデータを取得する
    time_min     = time_min.strftime("%Y-%m-%dT%H:%M:00.000000Z")
    access_token = "**********************************************"
    api          = API(access_token = access_token, environment="practice")
    request      = oandapy.InstrumentsCandles(instrument = "USD_JPY", params = { "alignmentTimezone": "Japan", "from": time_min, "count": minutes, "granularity": "M1" })
    api.request(request)

    candle = pandas.DataFrame.from_dict([ row['mid'] for row in request.response['candles'] ])
    candle = candle.set_index([[ row['time'] for row in request.response['candles'] ]])
    print(candle)