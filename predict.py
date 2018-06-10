
import technical_test
import time
import numpy as np

from pathlib import Path

import memcache
# sudo apt-get install memcached
# sudo pip3 install python-memcached

def print_and_write(a_string, filename = './autotrading_log'):
    print(a_string)

    time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    log_file = Path(filename)
    if log_file.is_file():
        with open(filename, 'a') as lf:
            lf.write('%s @ %s \n' % (a_string, time_str))
    else:
        with open(filename, 'w') as lf:
            lf.write('%s @ %s \n' % (a_string, time_str))



class Predict(technical_test.GMMA):
    def get_curr_cond_market_price(self, num=63, periods='15m'):
        (time_stamp, open_price, high_price, low_price, close_price) = self.btc_charts.get_price_array_till_finaltime(
            final_unixtime_stamp=time.time(), num=num, periods=periods, converter=True)
        (ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60) = self.get_GMMA(close_price)
        ema = np.c_[ema3, ema5, ema8, ema10, ema12, ema15, ema30, ema35, ema40, ema45, ema50, ema60]
        div_ratio = self.get_GMMA_divergence_ratio(ema)

        grad_w = self.get_GMMA_gradient(ema, periods)

        all = np.c_[
            time_stamp, open_price, high_price, low_price, close_price, ema, grad_w]

        #print(len(all))

        amount = np.zeros([len(all), 5])
        hold = False
        sell_price = []
        buy_price = []
        curtime = []
        for t in range(62, len(all)):
            # (gradient_real, grad_w_real)=self.get_current_GMMA_gradient_realtime(ema[t-1], all[t][2], periods)
            sell_price.append(self.get_sellprice(ema[t - 1], all[t][1], periods))
            buy_price.append(self.get_buyprice(ema[t - 1], all[t][1], periods))
            curtime.append(all[t][0])
        return [sell_price,buy_price,curtime]



if __name__ == '__main__':
    sleep_time = 1

    while(1):
        predict = Predict()
        result = predict.get_curr_cond_market_price(num=1000)
        curtime = str(result[2][-1])
        print_and_write('%s sell: %.0f , buy : %.0f'%(curtime, result[0][-1], result[1][-1]))
        storinmem = 0
        if storinmem: # store result in memeory
            shared = memcache.Client(['127.0.0.1:11211'], debug=0)
            shared.set('sellbuytime', result)
        print('Sleep %ds'%sleep_time)
        time.sleep(sleep_time)
