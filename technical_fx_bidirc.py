#!/usr/bin/python3
# coding=utf-8


import talib
import numpy as np
import historical_fx
import os
import pandas as pd
# import plot_chart as plc
import matplotlib.pyplot as plt
# from matplotlib.finance import candlestick_ohlc as plot_candle
import time


class HILO:
    def __init__(self):
        print("HILO initialized")
        self.btc_charts = historical_fx.charts()

    def MA(self, ndarray, timeperiod=5):
        x = np.array([talib.MA(ndarray.T[0], timeperiod)])
        # print(x)
        return x.T

    def get_HIGH_MA(self, HIGH):  # price=1*N (N>61)
        ma_high=self.MA(HIGH,35)
        return ma_high

    def get_LOW_MA(self, LOW):  # price=1*N (N>61)
        ma_low=self.MA(LOW,40)
        return ma_low

    def get_long_price(self, HIGH):
        ma_high=self.get_HIGH_MA(HIGH)
        return ma_high

    def get_short_price(self, LOW):
        ma_low = self.get_LOW_MA(LOW)
        return ma_low

    def publish_current_hilo_price(self, num=100, periods="1H"):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)

        low_price_ma = self.get_short_price(low_price)
        high_price_ma = self.get_long_price(high_price)
        (buyprice, sellprice)=(high_price_ma[-1][0],low_price_ma[-1][0])
        a=(int(buyprice), int(sellprice))
        print(a)
        return (int(buyprice), int(sellprice), int(close_price[-1]))

    def simulate(self, num=100, periods="1m" ,end_offset=0):
        mode=0  #0: both long and short;
                #1: only long;
                #2: only short;


        leverage = 1.0
        fee_ratio = 0.000  # trading fee percent
        ################Simulation#######################
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time() - end_offset, num=num, periods=periods, converter=True)


        all = np.c_[time_stamp, open_price, high_price, low_price, close_price]
        long_price = self.get_long_price(high_price)
        short_price = self.get_short_price(low_price)

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(len(long_price))
        print(len(short_price))


        amount = np.zeros([len(all), 7])
        long = False
        short = False
        cash = 10000.
        prev_cash=cash
        btc = 0.
        value = cash
        long_times = 0
        short_times = 0
        short_start_price= 0.
        long_start_price = 0.
        trade_back=0
        for t in range(50, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)
            #current hour's operation price initialization
            buy_price = long_price[t]
            sell_price = short_price[t]


            if not short and not long:
                if all[t][3] < sell_price:   #low price is lower than sell_price
                    #short starts
                    short = True
                    short_start_price = sell_price
                    trading_cash = cash
                    short_times += 1
                    amount[t][6] = 555
                    cash=0.

                    #Current hour processing
                    if all[t][4] > buy_price:
                        # short over
                        short = False
                        cash=(1+(short_start_price-buy_price)/short_start_price)*trading_cash
                        if cash < 0:
                            cash = 0
                        short_start_price = 0.
                        trading_cash = 0.

                        # long starts
                        long = True
                        long_start_price = buy_price
                        trading_cash = cash
                        long_times += 1
                        amount[t][5] = 888
                        cash = 0.
                elif all[t][2] > buy_price: # high price is higher than buy_price
                    # long starts
                    long = True
                    long_start_price = buy_price
                    trading_cash = cash
                    long_times += 1
                    amount[t][5] = 888
                    cash = 0.

                    #Current hour processing
                    if all[t][4] < sell_price:
                        # long over
                        long = False
                        cash=(1-(long_start_price-sell_price)/long_start_price)*trading_cash
                        if cash < 0:
                            cash = 0
                        long_start_price = 0.
                        trading_cash = 0.

                        # short starts
                        short = True
                        short_start_price = sell_price
                        trading_cash = cash
                        short_times += 1
                        amount[t][6] = 555
                        cash = 0.


            elif short and not long:
                if all[t][1]>buy_price:
                    buy_price=all[t][1]

                if all[t][4] > buy_price:  # close price is higher than reverse_price
                    # short over
                    short = False
                    cash = (1+(short_start_price-buy_price)/short_start_price)*trading_cash
                    if cash<0:
                        cash==0
                    short_start_price = 0.
                    trading_cash = 0.
                    amount[t][5] = 888

                    # long starts
                    long = True
                    long_start_price = buy_price
                    trading_cash = cash
                    cash = 0.
                    long_times += 1
                    amount[t][5] = 888
                else:
                    if all[t][2] > buy_price:
                        trade_back+=1

            elif not short and long:
                if all[t][1]<sell_price:
                    sell_price=all[t][1]

                if all[t][4] < sell_price:  # close price is lower than reverse_price
                    #long over
                    long = False
                    cash = (1 - (long_start_price - sell_price) / long_start_price) * trading_cash
                    if cash < 0:
                        cash == 0
                    long_start_price = 0.
                    trading_cash = 0.
                    amount[t][6] = 555

                    # short starts
                    short = True
                    short_start_price = sell_price
                    trading_cash = cash
                    cash=0.
                    short_times += 1
                    amount[t][6] = 555
                else:
                    if all[t][3] < sell_price:
                        trade_back+=1


            #result log
            if cash==0 and long:
                value = (1-(long_start_price-all[t][4])/long_start_price)*trading_cash
                if value<0:
                    print("Asset reset to zero")
                    break
            elif cash==0 and short:
                value = (1+(short_start_price-all[t][4])/short_start_price)*trading_cash
                if value<0:
                    print("Asset reset to zero")
                    break
            else:
                value = cash


            amount[t][0] = buy_price
            amount[t][1] = sell_price
            amount[t][2] = cash
            amount[t][3] = btc
            amount[t][4] = value
            print("value: %s" % value)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, long_price,short_price, amount]

        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10","11","12","13", "14"})

        print("============================")
        print(long_times)
        print(short_times)

        cwd = os.getcwd()
        data.to_csv(
            cwd + "_jpy.csv",
            index=True)

        print("trade_back= %s "  %trade_back)

        return value, trade_back


class GMMA:
    def __init__(self):
        print("GMMA initialized")
        self.btc_charts = historical_fx.charts()

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

        grad_w = np.zeros(2)
        w_short = np.matrix([0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0., 0., 0., 0., 0., 0.])
        w_long = np.matrix([0., 0., 0., 0., 0., 0., 0.2, 0.2, 0.2, 0.2, 0.1, 0.1])

        grad_w[0] = w_short * gradient[0].reshape(12, 1)
        grad_w[1] = w_long * gradient[0].reshape(12, 1)

        return (gradient, grad_w)

    def get_sellprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] < -0.2:
                break
            price -= delta

        return price

    def get_buyprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] > 0.2:
                break
            price += delta

        return price

    def get_divsellprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] > 15:
                break
            price += delta

        return price

    def get_divbuyprice(self, last_ema_all, current_open, periods):
        price = current_open

        delta = 1000
        for i in range(0, 100):
            (gradient, grad_w) = self.get_current_GMMA_gradient_realtime(last_ema_all, price, periods)
            if grad_w[0] < -100:
                break
            price -= delta

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
        w_short = np.matrix([0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0., 0., 0., 0., 0., 0.])
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

        print(all)
        print("all")
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
        return (buyprice, sellprice, grad_weighted)

    def lowest_in_rest_hour(self, final_unixtime, buy_price):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp = final_unixtime, num=3, periods="15m", converter=True)

        all=np.c_[time_stamp, open_price, high_price, low_price, close_price]

        print(all)

        assert open_price[0] <=buy_price
        for i in range(len(close_price)):
            low_price[i]<=buy_price
            break

        lowest_price=buy_price
        for j in range(i, len(close_price)):
            if low_price[i]<lowest_price:
                lowest_price=close_price[i]

        return lowest_price


    def simulate(self, num=100, periods="1m" ,end_offset=0):
        mode=0  #0: both long and short;
                #1: only long;
                #2: only short;

        retreat=1 #0: using sell_price;
                  #1: using buy_price;
        leverage = 1.0
        fee_ratio = 0.000  # trading fee percent
        ################Simulation#######################
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time() - end_offset, num=num, periods=periods, converter=True)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        div_ratio = self.get_GMMA_divergence_ratio(ema)
        grad_w = self.get_GMMA_gradient(ema, periods)
        all = np.c_[time_stamp, open_price, high_price, low_price, close_price, ema, grad_w]
        amount = np.zeros([len(all), 7])
        long = False
        short = False
        cash = 10000.
        prev_cash=cash
        btc = 0.
        value = cash
        long_times = 0
        short_times = 0
        short_start_price= 0.
        long_start_price = 0.
        counter=0
        for t in range(61, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)

            #current hour's operation price initialization
            buy_price = self.get_buyprice(ema[t - 1], all[t][1], periods)
            sell_price = self.get_sellprice(ema[t - 1], all[t][1], periods)
            div_sellprice = self.get_divsellprice(ema[t - 1], all[t][1], periods)
            if retreat==1:
                reverse_price = buy_price
            else:
                reverse_price = sell_price

            if not short and not long:
                if all[t][3] < sell_price and mode==0:   #low price is lower than sell_price
                    #short starts
                    short = True
                    short_start_price = sell_price
                    trading_cash = cash
                    short_times += 1
                    amount[t][6] = 555
                    cash=0.

                    #Current hour processing
                    if all[t][4] > reverse_price:
                        # short over
                        short = False
                        cash=(1+(short_start_price-reverse_price)/short_start_price)*trading_cash
                        if cash < 0:
                            cash = 0
                        short_start_price = 0.
                        trading_cash = 0.

                        # long starts
                        long = True
                        long_start_price = reverse_price
                        trading_cash = cash
                        long_times += 1
                        amount[t][5] = 888
                        cash = 0.
                elif all[t][2] > buy_price and mode==0: # high price is higher than buy_price
                    # long starts
                    long = True
                    long_start_price = buy_price
                    trading_cash = cash
                    long_times += 1
                    amount[t][5] = 888
                    cash = 0.

                    #Current hour processing
                    if all[t][4] < reverse_price:
                        # long over
                        long = False
                        cash=(1-(long_start_price-reverse_price)/long_start_price)*trading_cash
                        if cash < 0:
                            cash = 0
                        long_start_price = 0.
                        trading_cash = 0.

                        # short starts
                        short = True
                        short_start_price = reverse_price
                        trading_cash = cash
                        short_times += 1
                        amount[t][6] = 555
                        cash = 0.

                elif all[t][2] > buy_price and mode==1: # high price is higher than buy_price
                    # long starts
                    long = True
                    long_start_price = buy_price
                    trading_cash = cash
                    long_times += 1
                    amount[t][5] = 888
                    cash = 0.

                    # Current hour processing
                    if all[t][4] < reverse_price:
                        # long over
                        long = False
                        cash=(1-(long_start_price-reverse_price)/long_start_price)*trading_cash
                        if cash < 0:
                            cash == 0
                        long_start_price = 0.
                        trading_cash = 0.
                        amount[t][6] = 555
                elif all[t][3] < sell_price and mode==2:   #low price is lower than sell_price
                    #short starts
                    short = True
                    short_start_price = sell_price
                    trading_cash=cash
                    short_times += 1
                    amount[t][6] = 555
                    cash=0.

                    #Current hour processing
                    if all[t][4] > reverse_price:
                        # short over
                        short = False
                        cash=(1+(short_start_price-reverse_price)/short_start_price)*trading_cash
                        if cash < 0:
                            cash == 0
                        short_start_price = 0.
                        trading_cash = 0.
                        amount[t][5] = 888


            elif short and not long:
                if all[t][4] > reverse_price:  # close price is higher than reverse_price
                    # short over
                    short = False
                    cash = (1+(short_start_price-reverse_price)/short_start_price)*trading_cash
                    if cash<0:
                        cash==0
                    short_start_price = 0.
                    trading_cash = 0.
                    amount[t][5] = 888

                    if mode !=2:
                        #long starts
                        long = True
                        long_start_price = reverse_price
                        trading_cash = cash
                        cash=0.
                        long_times += 1
                        amount[t][5] = 888


            elif not short and long:
                if all[t][4] < reverse_price:  # close price is lower than reverse_price
                    #long over
                    long = False
                    cash = (1 - (long_start_price - reverse_price) / long_start_price) * trading_cash
                    if cash < 0:
                        cash == 0
                    long_start_price = 0.
                    trading_cash = 0.
                    amount[t][6] = 555

                    if mode != 1:
                        # short starts
                        short = True
                        short_start_price = reverse_price
                        trading_cash = cash
                        cash=0.
                        short_times += 1
                        amount[t][6] = 555


            #result log
            if cash==0 and long:
                value = (1-(long_start_price-all[t][4])/long_start_price)*trading_cash
                if value<0:
                    print("Asset reset to zero")
                    break
            elif cash==0 and short:
                value = (1+(short_start_price-all[t][4])/short_start_price)*trading_cash
                if value<0:
                    print("Asset reset to zero")
                    break
            else:
                value = cash


            amount[t][0] = buy_price
            amount[t][1] = sell_price
            amount[t][2] = cash
            amount[t][3] = btc
            amount[t][4] = value
            print("value: %s" % value)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60, grad_w, amount]

        data = pd.DataFrame(all,
                            columns={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                                     "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"})

        print("============================")
        print(long_times)
        print(short_times)

        cwd = os.getcwd()
        data.to_csv(
            cwd + "_jpy.csv",
            index=True)

        print(counter)

        return value, counter


if __name__ == '__main__':
    # directly

    btc_charts = historical_fx.charts()

    (time_stamp, open_price, high_price, low_price, close_price) = btc_charts.get_price_array_till_finaltime()

    # print(close_price)

    # gmma = GMMA()
    # # simulate the past 24 hours
    # gmma.simulate(num=24 * 7 * 1 + 61, periods="1H", end_offset=3600 * 24 * 7 * 0)

    hilo = HILO()
    # simulate the past 24 hours
    # hilo.simulate(num=24 * 7 * 1 + 20, periods="1H", end_offset=3600 * 24 * 7 * 0)


    # sum = 0.
    # counter_sum= 0
    # length = 3
    # for i in range(length):
    #     value,counter = gmma.simulate(num=24 * 30 * 1 + 61, periods="1H", end_offset=3600 * 24 * 30 * (i+3))
    #     sum = sum + value
    #     counter_sum = counter_sum+counter
    # # gmma.simulate(num=60*24*50+61, periods="1m", end_offset=0)
    # # a=gmma.publish_current_limit_price(periods="1H")
    #
    # print(sum / length)
    # print(counter_sum / length)

    sum = 0.
    counter_sum= 0
    length = 1
    for i in range(length):
        value,counter = hilo.simulate(num=24 * 7 * 15 + 50, periods="1H", end_offset=3600 * 24 * 7 * (i+0))
        sum = sum + value
        counter_sum = counter_sum+counter
    # hilo.simulate(num=60*24*50+61, periods="1m", end_offset=0)
    # a=hilo.publish_current_limit_price(periods="1H")

    print(sum / length)
    print(counter_sum / length)

    hilo.publish_current_hilo_price()
