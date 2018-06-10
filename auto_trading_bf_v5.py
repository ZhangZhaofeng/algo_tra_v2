from tradingapis.bitflyer_api import pybitflyer
from tradingapis.bitbank_api import public_api, private_api
from tradingapis.zaif_api.impl import ZaifPublicApi, ZaifTradeApi
from tradingapis.zaif_api.api_error import *
from tradingapis.quoine_api import client
import keysecret as ks
import time
import copy
import predict

from timeit import Timer
from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib

class SendMail:

    def __init__(self,address,username,passwd ):
        self.address = address
        self.username = username
        self.passwd = passwd
        self.s = smtplib.SMTP('smtp.gmail.com', 587)
        self.from_add = 'goozzfgle@gmail.com'
        self.connect_mail_server()

    def connect_mail_server(self):
        try:
            if self.s.ehlo_or_helo_if_needed():
                self.s.ehlo()
            self.s.starttls()
            self.s.ehlo()
            self.s.login(self.username, self.passwd)
            return 0
        except smtplib.SMTPNotSupportedError:
            self.s.login(self.username, self.passwd)
            return 0
        return 1

    def send_email(self, toaddress ,mesage):
        self.connect_mail_server()
        try:
            self.s.sendmail(self.from_add, toaddress, mesage)
            print('Send a mail to %s' % (toaddress))
        except smtplib.SMTPDataError:
            print('Can not send a mail, maybe reach the daily limition')


class AutoTrading:
    currency_jpy = 0 # jpy btc
    currency_btc = 0
    holdflag = False
    order_places = {
            'exist': False,
            'type': '',
            'id': '',
            'remain' : 0.0,
            'trade_price' : '',
            'slide': 0.0
        }
    tradeamount = 1000
    position = 0
    wave_times = 0
    everhold = False
    real_position = 0.0


    def __init__(self, holdflag = False, order_places = {'exist': False, 'type': '','id': 0,'remain' : 0.0, 'trade_price' : '', 'slide': 0.0}, tradeamount = 1000, position = 0.0):
        print("Initializing API")
        self.bitflyer_api = pybitflyer.API(api_key=str(ks.bitflyer_api), api_secret=str(ks.bitflyer_secret))
        self.holdflag = holdflag # if hold bitcoin
        self.order_places = order_places # specific an exist order
        self.tradeamount = tradeamount # init trade amount only if order not exist
        self.position = position # remain position (btc)
        self.initeverhold()

    def initeverhold(self):
        if self.holdflag == True:
            self.everhold = True
        else:
            self.everhold = False



    def trade_bitflyer_constoplimit(self, type, buysellprice, amount):
        product= 'FX_BTC_JPY'
        print('trade bitflyer')
        expire_time = 65
        if type == 'BUY' or type == 'buy':
            # order = self.quoinex_api.create_market_buy(product_id=5, quantity=str(amount), price_range=str(buysellprice))
            parameters =  [{ 'product_code' : product, 'condition_type' : 'STOP', 'side': 'BUY',
                            'size': str(amount), 'trigger_price': str(buysellprice)}]
            order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
        elif type == "SELL" or type == "sell":
            parameters = [{'product_code': product, 'condition_type': 'STOP', 'side': 'SELL',
                          'size': str(amount), 'trigger_price': str(buysellprice)}]
            order = self.bitflyer_api.sendparentorder(order_method='SIMPLE', minute_to_expire=expire_time, parameters=parameters)
        else:
            print("error!")
        return (order)

    def get_orders(self, status = ''):
        #order = self.quoinex_api.get_orders()
        #order = self.quoinex_api.get_orders(status, limit)
        #ACTIVE CANCELED
        product = 'FX_BTC_JPY'
        if status != '':
            order = self.bitflyer_api.getparentorders(product_code=product, parent_order_state=status)
        else:
            order = self.bitflyer_api.getparentorders(product_code=product, count=30)
        return (order)

    def get_orderbyid(self, id):
        product = 'FX_BTC_JPY'
        i = 20
        while i > 0:
            try:
            #order = self.bitflyer_api.getparentorder(product_code=product, parent_order_acceptance_id=id)
                orders = self.get_orders()
                for i in orders:
                    if i['parent_order_acceptance_id'] == id:
                        return (i)
                print('order not find')
                return({})
            except Exception:
                print('Server is fucked off ,try again')
                time.sleep(20)
                i -= 1
                continue
        print('Try too many times, failed')
        return({})

    def handel_partly_deal(self, order):
        # if order is partly dealed, the state should be 'COMPLETED' however executed size is not full size.
        if order['parent_order_state'] == 'COMPLETED' and order['executed_size'] != order['size']:
            if self.order_places['remain'] - order['executed_size'] >= 0.001:
                order['executed_size'] = self.order_places['remain']
        return(order)

    def cancle_order(self, id):
        product = 'FX_BTC_JPY'
        i = 20
        while i>0:
            try:
                statue = self.bitflyer_api.cancelparentorder(product_code=product, parent_order_acceptance_id=id)
                time.sleep(10)
                order = self.get_orderbyid(id)
                if order['parent_order_state'] == 'COMPLETED':
                    predict.print_and_write('Order completed')
                    return (0.0)

                if order['parent_order_state'] == 'CANCELED':
                    predict.print_and_write('Order cancelled')
                    remain_amount = float(order['cancel_size'])
                    return(remain_amount)
                else:
                    i -= 1
                    print('Try again cancelling')
                    continue
            except Exception:
                order = self.get_orderbyid(id)
                if order['parent_order_state'] == 'COMPLETED':
                    print('Executed before cancelling')
                    return(0.0)
                time.sleep(5)
                print('Exception Try again cancelling')
                i -= 1
        predict.print_and_write('Cancel order failed')
        self.sendamail('Cancel order failed','cancel failed : id %s'%(id))
        return([])

    def onTrick_trade(self, buyprice, sellprice, slide = 200):

        buyprice = float(buyprice)
        sellprice = float(sellprice)

        if self.order_places['exist']: # There is an order existed in last time
            placed = self.get_orderbyid(self.order_places['id'])
            placed = self.handel_partly_deal(placed)


            # detecting the order and get the information of this order
            if self.order_places['type'] == 'buy':
                self.position += placed['executed_size']
                self.tradeamount -= placed['executed_size'] * self.order_places['trade_price']
            elif self.order_places['type'] == 'sell':
                self.position -= placed['executed_size']
                self.tradeamount += placed['executed_size'] * self.order_places['trade_price']

            predict.print_and_write(
                'buy amount : %.3f sell amount : %.3f' % (self.position, self.tradeamount / buyprice))

            if self.order_places['remain'] - placed['executed_size'] < 0.001  : # if filled
                if self.order_places['type'] == 'buy': # if buy filled sell double
                    predict.print_and_write('Buy order filled')
                    self.holdflag = True
                    self.everhold = True
                    amount = self.position + self.position
                else:
                    predict.print_and_write('Sell order filled')
                    self.holdflag = False
                    amount = self.tradeamount / buyprice

                self.order_places['exist'] = False
                self.order_places['id'] = 0
                self.order_places['remain'] = .0

            else: # not filled or partly filled
                self.order_places['remain'] = self.cancle_order(self.order_places['id'])
                self.checkposition(placed)
                pflag = self.checkP()
                if pflag: # if position is unusuall
                    return(-1)
                # if a order is cancelled, but some trading happened between
                # detection and cancelling, the result may cause bug
                # it is necessary to check the cancel result and detection result and fix them
                self.order_places['exist'] = False
                self.order_places['id'] = 0
                predict.print_and_write('remain:%f'%(self.order_places['remain']))

                if self.order_places['remain'] < 0.001: # if filled
                    if self.order_places['type'] == 'buy':
                        predict.print_and_write('Buy order filled')
                        self.holdflag = True
                        self.everhold = True
                        amount = self.position + self.position
                    else:
                        predict.print_and_write('Sell order filled')
                        self.holdflag = False
                        amount = self.tradeamount / buyprice

                else: # not filled
                    if self.order_places['type'] == 'buy': #
                        predict.print_and_write('Buy order not filled buy again')
                        self.holdflag = False
                        amount = self.tradeamount / buyprice # continue buy
                        if amount < 0.001:
                            amount = 0.001
                        #
                    else: # treat as sell succeed
                        predict.print_and_write('Sell order not filled sell again')
                        self.holdflag = True
                        self.everhold = True
                        amount = self.order_places['remain'] # continue sell
                        if amount < 0.001:
                            amount = 0.001

                # maybe bug here cancelled but actually executed

        else:
            if self.holdflag:
                amount = self.tradeamount / sellprice
            else:
                amount = self.tradeamount / buyprice

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
                    new_order = self.trade_bitflyer_constoplimit(side, sellprice + slide, amount)
                    self.order_places['trade_price'] = sellprice
                    predict.print_and_write('Order placed sell %f @ %f'%(amount, sellprice))
                else:
                    new_order = self.trade_bitflyer_constoplimit(side, buyprice - slide, amount)
                    self.order_places['trade_price'] = buyprice
                    predict.print_and_write('Order placed buy %f @ %f' % (amount, buyprice))
                self.order_places['exist'] = True
                self.order_places['id'] = new_order['parent_order_acceptance_id']
                self.order_places['remain'] = amount
                self.order_places['type'] = side
                self.order_places['slide'] = slide

                predict.print_and_write('order: id %s, amount: %s, type: %s, price: %s'%(new_order['parent_order_acceptance_id'], str(amount), side, str(self.order_places['trade_price'])) )
                self.wave_times += 1
                return(self.order_places['id'])
            except Exception:
                print('Error! Try again')
                predict.print_and_write(new_order)
                time.sleep(5)
                try_times -= 1
        return(-2) # try too many times stop trading

    # check position of market
    def checkP(self):
        p = self.bitflyer_api.getpositions(product_code = 'FX_BTC_JPY')
        position0 = 0.0
        if isinstance(p, list):
            for i in p:
                if i['side'] == 'SELL':
                    position0 -= i['size']
                else:
                    position0 += i['size']
            if abs(position0 - self.position) < 0.001:
                predict.print_and_write('Real position is same as program one')
                return(0)
        if isinstance(p, dict) or len(p) == 0:
            if abs(self.position) < 0.001:
                predict.print_and_write('Position not exist')
                return (0)
        predict.print_and_write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        str = 'Position is unusual. Check!!! position :%f, program: %f'%(position0,self.position)
        predict.print_and_write(str)
        self.sendamail('position check failed', str)
        self.real_position = position0
        predict.print_and_write('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        return(1)

    # check position of market and program
    def checkposition(self,placed):
        product_code = 'FX_BTC_JPY'
        time.sleep(20)
        order0 = self.get_orderbyid(self.order_places['id'])
        x = order0['cancel_size']
        if abs(x - self.order_places['remain']) > 0.001:
            str = 'Order is unusual. Check!!! cancel size :%f, remain: %f' % (x, self.order_places['remain'])
            predict.print_and_write(str)
            self.sendamail('order check failed', str)

        amount = placed['size'] - placed['executed_size'] - self.order_places['remain']
        if abs(amount) > 0.001:
            predict.print_and_write('Trading occured during detecing and cancelling')
            if self.order_places['type'] == 'buy':
                predict.print_and_write('%f has been brought'%amount)
                self.position += amount
                self.tradeamount -= amount * self.order_places['trade_price']
            else:
                predict.print_and_write('%f has been sold'%amount)
                self.position -= amount
                self.tradeamount += amount * self.order_places['trade_price']


    def get_profit(self):
        balances = self.bitflyer_api.getbalance(product_code="FX_BTC_JPY")
        jpy_avai = 0.0
        btc_avai = 0.0
        for balance in balances:
            if balance['currency_code'] == 'JPY':
                jpy_avai = float(balance['available'])
            elif balance['currency_code'] == 'BTC':
                btc_avai = float(balance['available'])
        return ([jpy_avai, btc_avai])

    def get_collateral(self):
        balances = self.bitflyer_api.getcollateral()
        collateral = balances['collateral']
        openpnl = balances['open_position_pnl']
        return([collateral,openpnl])

    def sendamail(self, title ,str):
        address = 'goozzfgle@gmail.com'  # change the reciver e-mail address to yours
        username = 'goozzfgle@gmail.com'
        paswd = 'google871225'

        mail_str = '%s %s' % (str, formatdate(None, True, None))
        sender = SendMail(address, username, paswd)
        msg = MIMEText(mail_str)
        msg['Subject'] = title
        msg['From'] = username
        msg['To'] = address
        msg['Date'] = formatdate()
        sender.send_email(address, msg.as_string())



if __name__ == '__main__':
    tradeamount0 = 5000
    waiting_time = 3600
    detect_fre = 0 # detection frequency
    succeed = 0 # succeed times
    failed = 0 # failed times
    wait = 0 # waiting times
    maintance_time = 800
    if 1:
        order_places = {'exist' : False,'type' : '','id' : '','remain' : 0.0, 'trade_price' : 0.0}
        tradeamount0 = 8000
        position = 0.00
        holdflag = False
    elif 0: # if you want to recover the prcessing , input the detail of your order in following and change 'if 1' to 'if 0'
        order_places = {'exist': True, 'type': 'buy', 'id': 'JRF20180416-231608-353837', 'remain': 0.01,
                        'trade_price': 905432.0, 'slide': 200.0}
        tradeamount0 = 10000
        position = 0 # 0
        holdflag = False
    elif 0:
        # if buy order exist tradeamount should be 0
        order_places = {'exist': True, 'type': 'sell', 'id': 'JRF20180416-145646-706719', 'remain': 0.01,
                        'trade_price': 846725.0, 'slide': 0.0}
        tradeamount0 = 0
        position = 0.005
        holdflag = True
        # if sell order exist tradeamount should be
    autoTrading = AutoTrading(holdflag=holdflag, order_places=order_places, tradeamount=tradeamount0, position=position)
    prediction = predict.Predict()
    collateral = autoTrading.get_collateral()
    predict.print_and_write('Collateral: %f Profit: %f ' % (collateral[0], collateral[1]))
    tradingtimes = 0
    while 1:
        this_maintance_time = 0
        if tradingtimes > 0: # get the buy and sell price of last hour
            sell0 = sell
            buy0 = buy
            order0 = autoTrading.order_places['trade_price']
            position0 = autoTrading.position
            tradeamount0 = autoTrading.tradeamount
            everholdflag = autoTrading.everhold
            holdflag0 = autoTrading.holdflag
        result = prediction.publish_current_limit_price(periods="1H")
        predict.print_and_write('sell: %.0f , buy : %.0f' % (result[1], result[0]))
        sell = float(result[1])
        buy = float(result[0])
        close = float(result[2]) # the close price of last hour
        autoTrading.initeverhold() # initinal the ever hold flag before each iteration
        cur_oclock = int(time.strftime('%H:')[0:-1])
        cur_min = int(time.strftime('%M:')[0:-1])
        if (cur_oclock == 4 and cur_min >= 0 and cur_min <= 11) or (cur_oclock == 3 and cur_min >= 59):
            predict.print_and_write('Server maintenance')
            this_maintance_time = maintance_time
            time.sleep(this_maintance_time)

        oid = autoTrading.onTrick_trade(buy, sell, slide=200)  # trade first time
        if oid == -1 or oid == -2:
            print('oid : %d'%oid)
            break
        time.sleep(waiting_time - this_maintance_time)
        collateral = autoTrading.get_collateral()

        # record following thing of last 2 hour:
        # close price, buy price, sell price, btc remain, jpy remain
        if tradingtimes > 0:
            if holdflag0 :
                predict.print_and_write('Hold: close: %f, trade: %f, buy: %f sell: %f BTC: %f, JPY %f'%(close, order0, buy0, sell0, position0, tradeamount0))
            elif holdflag0==False :
                predict.print_and_write('Not hold: close: %f, trade: %f, buy: %f sell: %f BTC: %f, JPY %f' % (close, order0, buy0, sell0, position0, tradeamount0))
            if everholdflag:
                if close >= sell0 and holdflag0:
                    succeed += 1
                    predict.print_and_write('succeed:%d'%succeed)
                elif close <= sell0 and holdflag0 == False:
                    succeed += 1
                    predict.print_and_write('succeed:%d' % succeed)
                else:
                    failed += 1
                    predict.print_and_write('failed:%d' % failed)
            else:
                wait += 1
                predict.print_and_write('wait:%d' % wait)

        predict.print_and_write('Collateral: %f Profit: %f '%(collateral[0], collateral[1]))
        #predict.print_and_write('Trading jpy: %s btc: %s' % (str(autoTrading.tradeamount), str(autoTrading.position)))
        #predict.print_and_write('All jpy: %s btc: %s' % (str(float(cur_jpy)+ autoTrading.tradeamount), str(float(cur_btc) + autoTrading.position)))
        predict.print_and_write('==============================================')
        tradingtimes +=1