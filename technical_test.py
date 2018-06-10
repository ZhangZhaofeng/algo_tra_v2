#!/usr/bin/python3
# coding=utf-8


import talib
import numpy as np
import historical
import os
import pandas as pd
# import plot_chart as plc
import matplotlib.pyplot as plt
# from matplotlib.finance import candlestick_ohlc as plot_candle
import time


class GMMA:
    def __init__(self):
        print("GMMA initialized")
        self.btc_charts = historical.charts()

    def EMA(self, ndarray, timeperiod=4):
        x = np.array([talib.EMA(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_GMMA(self, price):  # price=1*N (N>61)
        ema3 = self.EMA(price, 3)
        ema5 = self.EMA(price, 5)
        ema8 = self.EMA(price, 8)
        ema10 = self.EMA(price, 10)
        ema12 = self.EMA(price, 12)
        ema15 = self.EMA(price, 15)
        ema30 = self.EMA(price, 30)
        ema35 = self.EMA(price, 35)
        ema40 = self.EMA(price, 40)
        ema45 = self.EMA(price, 45)
        ema50 = self.EMA(price, 50)
        ema60 = self.EMA(price, 60)

        return (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60)

    def get_current_ema_realtime(self, last_ema, current_price, N):
        return current_price * 2 / (N + 1) + last_ema * (N - 1) / (N + 1)

    def get_current_GMMA_realtime(self, last_ema_all, current_price):  # price=1*N (N>61)
        ema3 = self.get_current_ema_realtime(last_ema_all[0], current_price, 3)
        ema5 = self.get_current_ema_realtime(last_ema_all[1], current_price, 5)
        ema8 = self.get_current_ema_realtime(last_ema_all[2], current_price, 8)
        ema10 = self.get_current_ema_realtime(last_ema_all[3], current_price, 10)
        ema12 = self.get_current_ema_realtime(last_ema_all[4], current_price, 12)
        ema15 = self.get_current_ema_realtime(last_ema_all[5], current_price, 15)
        ema30 = self.get_current_ema_realtime(last_ema_all[6], current_price, 30)
        ema35 = self.get_current_ema_realtime(last_ema_all[7], current_price, 35)
        ema40 = self.get_current_ema_realtime(last_ema_all[8], current_price, 40)
        ema45 = self.get_current_ema_realtime(last_ema_all[9], current_price, 45)
        ema50 = self.get_current_ema_realtime(last_ema_all[10], current_price, 50)
        ema60 = self.get_current_ema_realtime(last_ema_all[11], current_price, 60)

        return np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]

    def get_current_GMMA_gradient_realtime(self, last_ema_all, current_price, periods):
        current_ema_all = self.get_current_GMMA_realtime(last_ema_all, current_price)
        gradient = np.zeros([1, 12])

        # print(current_ema_all)

        for i in range(0, 12):
            gradient[0][i] = (current_ema_all[0][i] - last_ema_all[i]) / float(
                self.btc_charts.period_converter(periods))

        grad_w = np.zeros(12)
        w_short = np.matrix([0.1, 0.1, 0.1, 0.2, 0.2, 0.3, 0., 0., 0., 0., 0., 0.])
        w_long = np.matrix([0., 0., 0., 0., 0., 0., 0.2, 0.2, 0.2, 0.2, 0.1, 0.1])

        grad_w[0] = w_short * gradient[0].reshape(12, 1)
        grad_w[1] = w_long * gradient[0].reshape(12, 1)

        return (gradient, grad_w)

    def get_sellprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 1000):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] < -0.2:
                break
            price -= delta

        return price

    def get_buyprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 1000):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] > 0.2:
                break
            price += delta

        return price

    def get_GMMA_gradient(self, ema, periods):
        assert (len(ema) > 61)
        gradient = np.zeros([len(ema), 12])
        # print(gradient)

        # compute gradient for 12 EMA lines respectively.
        for t in range(61, len(ema)):
            for i in range(0, 12):
                gradient[t][i] = (ema[t][i] - ema[t - 1][i]) / float(self.btc_charts.period_converter(periods))
                # print("grad=",gradient[t][i])

        # compute weighted composite gradients for both 6 long and 6 short EMA lines, respectively.
        grad_w = np.zeros([len(ema), 2])
        w_short = np.matrix([0.1, 0.1, 0.1, 0.2, 0.2, 0.3, 0., 0., 0., 0., 0., 0.])
        w_long = np.matrix([0., 0., 0., 0., 0., 0., 0.2, 0.2, 0.2, 0.2, 0.1, 0.1])

        for t in range(len(gradient)):
            grad_w[t][0] = w_short * gradient[t].reshape(12, 1)
            grad_w[t][1] = w_long * gradient[t].reshape(12, 1)

        return grad_w

    def get_GMMA_divergence_ratio(self, ema):
        short_term_gmma, long_term_gmma = np.hsplit(ema, [6])
        divergence_ratio = np.zeros([len(ema), 2])
        for t in range(61, len(ema)):
            divergence_ratio[t][0] = max(short_term_gmma[t]) / min(short_term_gmma[t])
            divergence_ratio[t][1] = max(long_term_gmma[t]) / min(long_term_gmma[t])

        return divergence_ratio

    def plot_chart_tillnow_to_csv(self, num=100, periods="1m"):
        while 1:
            try:
                (time_stamp, open_price, high_price, low_price,
                 close_price) = self.btc_charts.get_price_array_till_finaltime(num=num, periods=periods,
                                                                               converter=False)
                (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(
                    close_price)
                ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
                break
            except Exception:
                continue

        plot_all = np.c_[
            time_stamp, open_price.astype(int), high_price.astype(int), low_price.astype(int), close_price.astype(int)]
        # print(ema)

        figure, ax = plt.subplots()
        # plot_candle(ax, plot_all, width=0.4, colorup='#77d879', colordown='#db3f3f')
        plt.plot(time_stamp, ema)
        plt.show()

    def save_chart_tillnow_to_csv(self, num=62, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            num=num, periods=periods, converter=False)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]

        #print(all)
        #print("all")
        cwd = os.getcwd()
        data.to_csv(
            cwd + ".csv",
            index=True)

    def publish_current_limit_price(self, num=100, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        ema_latest_hour = ema[len(ema) - 1]
        open_curr = close_price[len(close_price) - 1]

        [a,b]=self.get_current_GMMA_gradient_realtime(ema_latest_hour.astype(float), open_curr.astype(float), periods)
        grad_weighted=b[0]
        sellprice = self.get_sellprice(ema_latest_hour.astype(float), open_curr.astype(float), periods)
        buyprice = self.get_buyprice(ema_latest_hour.astype(float), open_curr.astype(float), periods)
        print("Current grad_weighted= %s" %b[0])
        print([time_stamp[len(time_stamp) - 1], open_curr[0], buyprice[0], sellprice[0]])
        return (buyprice, sellprice, close_price[-1] ,grad_weighted)

    def simulate(self, num=100, periods="1m"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time() - 3600, num=num, periods=periods, converter=True)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        div_ratio = self.get_GMMA_divergence_ratio(ema)

        grad_w = self.get_GMMA_gradient(ema, periods)

        all = np.c_[time_stamp, open_price, high_price, low_price, close_price, ema, grad_w]

        # print(len(all))

        amount = np.zeros([len(all), 5])
        hold = False
        cash = 10000.
        btc = 0.
        value = cash
        buy_times = 0
        sell_times = 0
        for t in range(62, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)
            sell_price = self.get_sellprice(ema[t - 1], all[t][1], periods)
            buy_price = self.get_buyprice(ema[t - 1], all[t][1], periods)

            #print(ema[t - 1])
            if hold == False:
                # if all[t][17] > 0.1 and all[t][17] < 1.3 and all[t][18] > 0.0 and div_ratio[t][0]<1.05 :
                if all[t][2] > buy_price :  # and #all[t-1][18] > 0.0:  #high price is higher than buy_price
                    hold = True
                    btc = cash / buy_price
                    cash = 0.
                    buy_times += 1
            elif hold == True:
                assert (all[t][1] >= sell_price)
                if all[t][3] < sell_price :  # low price is lower than sell_price
                    hold = False
                    cash = sell_price * btc
                    btc = 0.
                    sell_times += 1

            value = cash + all[t][4] * btc
            amount[t][0] = buy_price
            amount[t][1] = sell_price
            amount[t][2] = cash
            amount[t][3] = btc
            amount[t][4] = value
            #print("value: %s" % value)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60, grad_w, amount]

        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                                     "16", "17", "18", "19", "20", "21", "22", "23", "24"})

        print("============================")
        print(buy_times)
        print(sell_times)

        cwd = os.getcwd()
        data.to_csv(
            cwd + ".csv",
            index=True)


if __name__ == '__main__':
    # directly

    btc_charts = historical.charts()

    (time_stamp, open_price, high_price, low_price, close_price) = btc_charts.get_price_array_till_finaltime()

    # print(close_price)

    gmma = GMMA()
    # gmma.save_chart_tillnow_to_csv(num=1000, periods="1H")
    #
    a=gmma.publish_current_limit_price(periods="1H")
    gmma.simulate(num=24 * 7 * 30 + 61, periods="1H")