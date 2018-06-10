from tradingapis.bitflyer_api import pybitflyer
import keysecret as ks
import time
import predict
import configIO
import sys
import math
import data2csv



class AutoTrading:
    amount = 0.02
    mid_prices = [0,0,0,0]
    mid_price_index = 0


    def __init__(self):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))

    def maintance_time(self):
        while 1:
            cur_oclock = int(time.strftime('%H:')[0:-1])
            cur_min = int(time.strftime('%M:')[0:-1])
            if (cur_oclock == 4 and cur_min >= 0 and cur_min <= 12) or (cur_oclock == 3 and cur_min >= 58):
                predict.print_and_write('Server maintenance')
                time.sleep(60)
                continue
            else:
                return

    def trade_simple(self, buy, sell, amount = amount):
        self.maintance_time()

        product = 'FX_BTC_JPY'
        print('trade bitflyer, buy: %f, sell %f'%(buy, sell))
        expire_time = 75
        order = self.bitflyer_api.sendchildorder(product_code='FX_BTC_JPY',
                                                     child_order_type='LIMIT',
                                                     side="BUY",
                                                     size=amount,
                                                     price= '%.0f'%buy,
                                                     minute_to_expire=75)
        data2csv.data2csv(
                [time.strftime('%b:%d:%H:%M'), 'order', 'BUY_LIMIT', 'amount', '%f' % float(amount), 'limit',
                 '%f' % float(buy)])
        time.sleep(1)
        print(order)
        order = self.bitflyer_api.sendchildorder(product_code='FX_BTC_JPY',
                                                  child_order_type='LIMIT',
                                                  side='SELL',
                                                  size=amount,
                                                  price='%.0f'%sell,
                                                  minute_to_expire=75)
        data2csv.data2csv(
                [time.strftime('%b:%d:%H:%M'), 'order', 'SELL_LIMIT', 'amount', '%f' % float(amount), 'limit',
                 '%f' % float(sell)])
        print(order)

    def get_depth(self):
        depth =self.bitflyer_api.board(product_code = 'FX_BTC_JPY', count = 100)
        return(depth)

    def cal_depth_twoside(self,depth):
        asks = depth['asks']
        bids = depth['bids']
        ask_size = 0.0
        bid_size = 0.0
        for i in asks[:30]:
            ask_size += i['size']

        for j in bids[:30]:
            bid_size += j['size']


        return([ask_size, bid_size])

    def get_current_price(self):
        trade_history = self.bitflyer_api.executions(product_code = 'FX_BTC_JPY', count = 1000)
        total_size = 0.0
        cur_price = 0.0
        last_price = []
        for i in trade_history:
            last_price.append(i['price'])
        return(last_price)

    def judge_market(self, ask_bid_size):
        #1. judge if bull or bear
        last_price = self.get_current_price()
        margin1 = last_price[0] * 0.00005
        bull = False
        bear = False

        if last_price[0] > max(last_price[1:200]) + margin1:
            print('bull')
            bull = True
        elif last_price[0] < min(last_price[1:200]) - margin1:
            print('bear')
            bear = True

        if bull or bear:
            return (False)

        print('ask: % f, bid % f'%(ask_bid_size[0], ask_bid_size[1]))
        if (ask_bid_size[0]> 20 or ask_bid_size[1]>20) and (ask_bid_size[0]/ask_bid_size[1] > 2.3 or ask_bid_size[1]/ask_bid_size[0] > 2.3):
            print('Over trading')
            return (False)

        rsi = self.get_rsi(last_price)
        print('rsi: %f'%rsi)

        if rsi <= 20 or rsi >= 80:
            print('Obvious trend')
            return (False)


        return(True)

    def get_rsi(self, lastprice):
        gain = 0.0
        loss = 0.0
        first_window = lastprice[-15:]
        others = lastprice[:-16]
        price_list_len = 15
        flag = 1
        for i in first_window[0:15]:
            if flag < price_list_len:
                diff = i - lastprice[flag]
                if diff > 0:
                    gain += diff * 1/14
                else:
                    loss += -diff* 1/14
                flag += 1


        gains = []
        losses = []
        gains.append(gain)
        losses.append(loss)
        others_len = len(others)
        for j in range(0, others_len):
            cur_index = others_len -j -1
            diff = lastprice[cur_index] - lastprice[cur_index+1]
            if diff > 0:
                gain = (gain * 13 + diff) / 14
                loss = (loss * 13) / 14
            else:
                loss = (loss * 13 - diff) / 14
                gain = (gain * 13) / 14
            gains.append(gain)
            losses.append(loss)


        if loss == 0.0:
            loss = 0.001
        rs = gain / loss
        rsi = 100-(100/(1+rs))
        return(rsi)

    def judge_if_enough_mergin(self, ref_price, amount = amount*2):
        result = self.bitflyer_api.getcollateral()
        last_collateral = result['collateral'] -  result['require_collateral']
        predict.print_and_write('collateral: %f, last collateral: %f'%(result['collateral'], last_collateral))
        if last_collateral > ref_price * amount * 1.001:
            return(True)
        else:
            return(False)

    def get_price(self, depth, if123=False):
        asks = depth['asks'][:30]
        bids = depth['bids'][:30]

        sell_price = float(asks[0]['price'])
        buy_price = float(bids[0]['price'])
        sell_price1 = sell_price
        buy_price1 = buy_price
        sell_price2 = float(asks[1]['price'])
        buy_price2 = float(bids[1]['price'])
        sell_price3 = float(asks[2]['price'])
        buy_price3 = float(bids[2]['price'])
        amount_asks = 0.0
        amount_bids = 0.0
        largest_diff = 200
        mini_diff = 50
        float_amount_buy = 0.1
        float_amount_sell = 0.1
        buy_depth = 0.0
        sell_depth = 0.0

        for i in range(0, 30):
            sell_depth += float(asks[i]['size'])
            buy_depth += float(bids[i]['size'])

        len_a = len(asks)
        for i in range(0, len_a):
            amount_asks += float(asks[i]['size'])
            if amount_asks > float_amount_sell:
                sell_price = float(asks[i]['price']) - 3.0
                break

        len_b = len(bids)
        for i in range(0, len_b):
            amount_bids += float(bids[i]['size'])
            if amount_bids > float_amount_buy:
                buy_price = float(bids[i]['price']) + 3.0
                break

        ave_price = (sell_price1 + buy_price1) / 2 * 0.7 + (sell_price2 + buy_price2) / 2 * 0.2 + (
                                                                                                  sell_price3 + buy_price3) / 2 * 0.1
        mid_price = (sell_price1 + buy_price1) / 2
        if sell_price - mid_price > largest_diff:
            sell_price = mid_price + largest_diff
        if mid_price - buy_price > largest_diff:
            buy_price = mid_price - largest_diff

        if sell_price - mid_price < mini_diff:
            sell_price = mid_price + mini_diff
        if mid_price - buy_price < mini_diff:
            buy_price = mid_price - mini_diff

            sell_price = float('%.2f' % sell_price)
            buy_price = float('%.2f' % buy_price)

        if if123:
            return (ave_price, sell_depth, buy_depth)
        else:
            return ([buy_price, sell_price])


    def get_checkin_price(self):
        p = self.bitflyer_api.getpositions(product_code='FX_BTC_JPY')
        position0 = 0.0
        checkin_price = 0.0
        if isinstance(p, list):
            for i in p:
                #predict.print_and_write('check in price: %f' % (i['price']))

                if i['side'] == 'SELL':
                    position0 -= i['size']
                else:
                    position0 += i['size']

            for i in p:
                checkin_price += i['size']/abs(position0) * i['price']
            predict.print_and_write('Check in price: %f, position: %f' % (checkin_price, position0))


        elif isinstance(p, dict) or len(p) == 0:
            predict.print_and_write('Position not exist')

        return([checkin_price, position0])

    def trade_checkin(self, checkin_price, position):
        loss_factor = 0.002
        if position > 0:
            type = 'SELL'
            loss_cut = checkin_price * (1- loss_factor)
        elif position < 0:
            type = 'BUY'
            loss_cut = checkin_price * (1 + loss_factor)

        product = 'FX_BTC_JPY'
        print('trade bitflyer, %s: %f' % (type, position))
        expire_time = 999

        parameters = [{'product_code': product, 'condition_type': 'LIMIT', 'side': type,
                       'size': '%.2f'%abs(position), 'price': '%.0f' % checkin_price},
                      {'product_code': product, 'condition_type': 'STOP', 'side': type,
                       'size': '%.2f'%abs(position), 'trigger_price': '%.0f' %loss_cut},
                      ]
        order = self.bitflyer_api.sendparentorder(order_method='OCO', minute_to_expire=expire_time,
                                                  parameters=parameters)
        print(order)

    def judge_mid_price(self, mid_price):

        if self.mid_price_index > 3:
            diff = [0,0,0]
            self.mid_prices[0] = self.mid_prices[1]
            self.mid_prices[1] = self.mid_prices[2]
            self.mid_prices[2] = self.mid_prices[3]
            self.mid_prices[3] = mid_price
            diff[0] = self.mid_prices[1] - self.mid_prices[0]
            diff[1] = self.mid_prices[2] - self.mid_prices[1]
            diff[2] = self.mid_prices[3] - self.mid_prices[2]
            if (diff[0]>0 and diff[1] > 0 and diff[2] > 0 ) or (diff[0]<0 and diff[1] < 0 and diff[2] < 0 ):
                if abs(diff[0] + diff[1] + diff[2]) > 300:
                    print('Big change')
                    return False
        else:
            self.mid_prices[self.mid_price_index] = mid_price
            self.mid_price_index += 1
        return True

        self.mid_price_index += 1



if __name__ == '__main__':
    stop_flag = 0
    at = AutoTrading()
    while 1:


        checkins = at.get_checkin_price()
        print(checkins)
        depth = at.get_depth()
        ask_bid_size = at.cal_depth_twoside(depth)
        #r = at.judge_market(ask_bid_size)

        results = at.get_price(depth, if123=False)
        sell = results[1]
        buy = results[0]


        mid_price = (sell + buy) / 2

        enough_mergin = at.judge_if_enough_mergin(mid_price)
        if at.judge_market(ask_bid_size) and enough_mergin and at.judge_mid_price(mid_price):
            at.trade_simple(buy, sell)
            stop_flag = 0
        elif not enough_mergin:
            print('Mergin is not enough')
            stop_flag +=1
            if stop_flag > 1:
                at.bitflyer_api.cancelallchildorders(product_code = 'FX_BTC_JPY')
                time.sleep(20)

                at.trade_checkin(checkins[0], checkins[1])
                time.sleep(20)
                while not at.judge_if_enough_mergin(mid_price):
                    print('waiting for trade off')
                    time.sleep(20)
                stop_flag = 0
        print(results)
        i = 1
        while i < 4:
            print('.')
            time.sleep(5)
            i += 1