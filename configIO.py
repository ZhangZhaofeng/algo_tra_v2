import configparser
import time
import sys

class configIO():
    def __init__(self, config_file = './last_trade.ini'):
        self.config = configparser.ConfigParser()
        self.config_file = config_file

    def read_config_order(self):
        self.config.read(self.config_file)
        for key in self.config:
            if key == 'order':
                previous_order = dict()
                #labels = ['exist', 'type', 'id', 'remain', 'trade_price', 'slide', 'tradeamount','position', 'holdflag']
                previous_order['exist'] = bool(self.config.get(key, 'exist'))
                previous_order['remain'] = float(self.config.get(key, 'remain'))
                previous_order['id'] = str(self.config.get(key, 'id'))
                previous_order['type'] = str(self.config.get(key, 'type'))
                previous_order['trade_price'] = float(self.config.get(key, 'trade_price'))
                previous_order['slide'] = float(self.config.get(key, 'slide'))
                previous_order['tradeamount'] = float(self.config.get(key, 'tradeamount'))
                previous_order['position'] = float(self.config.get(key, 'position'))
                previous_order['holdflag'] = bool(self.config.get(key, 'holdflag'))
                previous_order['slide'] = float(self.config.get(key, 'slide'))
                return(previous_order)
        return({})

    def save_config_order(self, configs):
        if isinstance(configs, dict):
            self.config.read_dict(configs)
            with open (self.config_file, 'w') as inifile:
                self.config.write(inifile)
            return(0)
        return(1)

if __name__ == '__main__':


    argvs = sys.argv
    argc = len(argvs)

    if argc >=2 :
        cofile = sys.argv[1]
        cf = configIO(config_file = cofile)
    else:
        cf = configIO()

    tempcf = dict()
    tempcf['order'] =  {'exist': True, 'type': 'sell', 'id': 'JRF20180416-145646-706719', 'remain': 0.01,
                        'trade_price': 846725.0, 'slide': 0.0, 'tradeamount': 0.0,'position': 0.033, 'holdflag':True,
                        'timestamp':time.strftime('%b-%d/%H:%M:%S'),'slide':200}
    result = cf.save_config_order(tempcf)
    cf.read_config_order()


