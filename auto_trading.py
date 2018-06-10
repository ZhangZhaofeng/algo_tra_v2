
from tradingapis.bitflyer_api import pybitflyer
from tradingapis.bitbank_api import public_api, private_api
from tradingapis.zaif_api.impl import ZaifPublicApi, ZaifTradeApi
from tradingapis.zaif_api.api_error import *
from tradingapis.quoine_api import client
import keysecret as ks
import time
import copy
import predict




class AutoTrading:
    currency_jpy = 0 # jpy btc
    currency_btc = 0
    holdflag = False
    order_places = {
            'exist': False,
            'type': '',
            'id': 0,
            'remain' : 0.0
        }
    tradeamount = 1000



    def __init__(self, holdflag = False, order_places = {'exist': False,'type': '','id': 0,'remain' : 0.0}, tradeamount = 1000):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))
        #self.zaif_api = ZaifTradeApi(key=str(ks.zaif_api), secret=str(ks.zaif_secret))
        self.quoinex_api = client.Quoinex(api_token_id=str(ks.quoinex_api), api_secret=(ks.quoinex_secret))
        #self.bitbank_api = private_api.bitbankcc_private(api_key=str(ks.bitbank_api), api_secret=str(ks.bitbank_secret))
        self.holdflag = holdflag
        self.order_places = order_places
        self.tradeamount = tradeamount

    def trade_quoine_condmarket(self, type, buysellprice ,amount):
        print("trade_quoine")
        if type == 'BUY' or type == 'buy':
            #order = self.quoinex_api.create_market_buy(product_id=5, quantity=str(amount), price_range=str(buysellprice))
            order = self.quoinex_api.create_order(order_type='stop', product_id=5, side='buy', quantity=str(amount), price=str(buysellprice))
        elif type == "SELL" or type == "sell":
            order = self.quoinex_api.create_order(order_type='stop', product_id=5, side='sell', quantity=str(amount), price=str(buysellprice))
        else:
            print("error!")
        return(order)



    #def get_balance(self):

    def get_orders(self, status = 'live', limit = 10):
        #order = self.quoinex_api.get_orders()
        order = self.quoinex_api.get_orders(status, limit)
        return (order)

    def get_orderbyid(self, id):
        try:
            order = self.quoinex_api.get_order(id)
            return (order)
        except Exception:
            print('Server is fucked off , search order by another way')
            time.sleep(20)
            orders = self.quoinex_api.get_orders(limit= 20)
            for i in orders['models']:
                if i['id'] == id:
                    return(i)

    def cancle_order(self, id):
        try:
            checkid = self.quoinex_api.cancel_order(id)
            remain_amount = float(checkid['quantity']) - float(checkid['filled_quantity'])
            return(remain_amount)
        except Exception:
            time.sleep(5)
            order = self.quoinex_api.get_orders(limit=40)
            for i in order['models']:
                if i['status'] == 'live':
                    checkid = self.quoinex_api.cancel_order(i['id'])
                    print('cancel a order id %d'%(i['id']))
                    remain_amount = float(checkid['quantity']) - float(checkid['filled_quantity'])
                    return(remain_amount)
            print('Filled before cancelling')
            return(0.0)

    def onTrick_trade(self, buyprice, sellprice, avg_open):

        buyprice = float(buyprice)
        sellprice = float(sellprice)
        tradeamount = float(self.tradeamount)

        if self.order_places['exist']: # if there is a order detect if it filled or not yet

            placed = self.get_orderbyid(self.order_places['id'])

            if placed['status'] == 'filled':
                #avg_price = float(placed['average_price'])
                self.order_places['exist'] = False
                self.order_places['id'] = 0
                self.order_places['remain'] = .0

                if self.order_places['type'] == 'buy':
                    predict.print_and_write('Buy order filled')
                    self.holdflag = True
                    amount = tradeamount / sellprice
                else:
                    predict.print_and_write('Sell order filled')
                    self.holdflag = False
                    amount = tradeamount / buyprice

            else: # not filled or partly filled
                self.order_places['remain'] = self.cancle_order(self.order_places['id'])
                self.order_places['exist'] = False
                self.order_places['id'] = 0

                if self.order_places['remain'] < 0.001: # little remain treat as buy succeed
                    if self.order_places['type'] == 'buy': #
                        predict.print_and_write('Buy order filled remain %f'%self.order_places['remain'])
                        self.holdflag = True
                        amount = tradeamount / sellprice - self.order_places['remain']
                        if amount < 0.001:
                            amount = 0.001
                    else: # treat as sell succeed
                        predict.print_and_write('Sell order filled remain %f'%self.order_places['remain'])
                        self.holdflag = False
                        amount = tradeamount / buyprice - self.order_places['remain']
                        if amount < 0.001:
                            amount = 0.001

                else: # partly filled and large remain treat as buy failed
                    if self.order_places['type'] == 'buy': #
                        predict.print_and_write('Buy order not filled buy again')
                        self.holdflag = False
                        amount = self.order_places['remain'] # continue buy
                        if amount < 0.001:
                            amount = 0.001
                        #
                    else: # treat as sell succeed
                        predict.print_and_write('Sell order not filled sell again')
                        self.holdflag = True
                        amount = self.order_places['remain'] # continue sell
                        if amount < 0.001:
                            amount = 0.001

        else:
            if self.holdflag:
                amount = tradeamount / sellprice
            else:
                amount = tradeamount / buyprice

        if self.holdflag:
            side = 'sell'
        else:
            side = 'buy'


        amount = float(str('%.3f'%amount))
        if amount < 0.001:
            print('less than min amount')
            return(-1) # less than min amount stop trading

        try_times = 20
        while try_times > 0:
            try:
                if side == 'sell':
                    new_order = self.trade_quoine_condmarket(side, sellprice, amount)
                    predict.print_and_write('Order placed sell %f @ %f'%(amount, sellprice))
                else:
                    new_order = self.trade_quoine_condmarket(side, buyprice, amount)
                    predict.print_and_write('Order placed buy %f @ %f' % (amount, buyprice))
                self.order_places['exist'] = True
                self.order_places['id'] = new_order['id']
                self.order_places['remain'] = amount
                self.order_places['type'] = side
                return(self.order_places['id'])
            except Exception:
                print('Error! Try again')
                continue
                try_times -= 1

        return(-2) # try too many times stop trading

    def bitf2qix(self, buy,sell):
        try:
            bid_mix_b = 0.0
            bid_mix_q = 0.0
            ask_mix_b = 0.0
            ask_mix_q = 0.0
            for i in range(0,10):
                bid_mix_b += float(self.get_bid_ask_bitflyer()[0])*0.1
                ask_mix_b += float(self.get_bid_ask_bitflyer()[1])*0.1
                bid_mix_q += float(self.get_bid_ask_quoine()[0])*0.1
                ask_mix_q += float(self.get_bid_ask_quoine()[1])*0.1
                time.sleep(1)
            sell = sell + bid_mix_q - bid_mix_b
            buy = buy + ask_mix_q - ask_mix_b

            sell = float(str('%.0f'%sell))
            buy = float(str('%.0f'%buy))
            predict.print_and_write('use adjusted price : buy %f sell %f' %(buy, sell))
            return [buy, sell]
        except Exception:
            print('Expection while adjusting buy sell price, use default value')
            return [buy, sell]

    def get_open(self):
        try:
            cur_time = time.strftime('%M:%S')
            spend = (int(cur_time[0])*10 + int(cur_time[1]))*60 + int(cur_time[3])*10 + int(cur_time[4])
            since = int(time.time()) -spend
            executions = self.quoinex_api.get_executions_since_time(
                product_id=5,
                timestamp=since,
                limit=20)
            avg_open_price = 0.0
            for i in executions:
                avg_open_price += float(i['price'])
            avg_open_price /= 20
            return avg_open_price
        except Exception:
            print('Expection while adjusting buy sell price, use default value')
            return 0.0


    def get_profit(self):
        balances = self.quoinex_api.get_account_balances()
        jpy_avai = 0.0
        btc_avai = 0.0
        for balance in balances:
            if balance['currency'] == 'BTC':
                btc_avai = float(balance['balance'])
            elif balance['currency'] == 'JPY':
                jpy_avai = float(balance['balance'])
        return ([jpy_avai, btc_avai])

    def get_bid_ask_bitflyer(self, product_pair='BTC_JPY'):
        if product_pair == '':
            product_pair = 'BTC_JPY'
        elif product_pair == 'BTC_ETH':
            product_pair = 'ETH_BTC'
        elif product_pair == 'BTC_LTC':
            product_pair = 'LTC_BTC'
        bitflyer_api = pybitflyer.API()
        jsons_dict = bitflyer_api.ticker(product_code='%s' % (product_pair))
        bid = jsons_dict['best_bid']
        ask = jsons_dict['best_ask']
        return [bid, ask]

    def get_bid_ask_quoine(self, product_pair='BTC_JPY'):
        if product_pair == 'BTC_JPY':
            product_pair = 5
        else:
            product_pair = ''

        quoine_api = client.Quoine()
        jsons_dict = quoine_api.get_product(product_pair)
        bid = jsons_dict['market_bid']
        ask = jsons_dict['market_ask']
        return ([bid, ask])


if __name__ == '__main__':
    autoTrading = AutoTrading(holdflag=True, order_places={'exist':True,'type':'buy','id':236894220,'remain':0.0}, tradeamount=60000)
    prediction = predict.Predict()
    profits = autoTrading.get_profit()
    init_jpy = profits[0]
    init_btc = profits[1]
    predict.print_and_write('Profit jpy: %s btc: %s'%(init_jpy, init_btc))

    while 1:
        result = prediction.publish_current_limit_price(periods="1H")
        predict.print_and_write('sell: %.0f , buy : %.0f' % (result[1], result[0]))
        sell = float(result[1])
        buy = float(result[0])
        #adjust_result = autoTrading.bitf2qix(buy, sell)
        #avg_open = autoTrading.get_open()
        #oid = autoTrading.onTrick_trade(adjust_result[0], adjust_result[1], avg_open) # buy ,sell
        oid = autoTrading.onTrick_trade(buy, sell, 0)  # buy ,sell
        #order = autoTrading.cancle_order(235147969)
        #order = autoTrading.get_orderbyid(235147969)
        if oid == -1 or oid == -2:
            print(oid)
            break
        print('wait 60 min')
        time.sleep(60*60)
        profits = autoTrading.get_profit()
        cur_jpy = profits[0]
        cur_btc = profits[1]
        predict.print_and_write('Profit jpy: %s btc: %s' % (cur_jpy, cur_btc))
