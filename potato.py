import ccxt
import time
import sys
import logging
import json
import os

import keys  # import API key and secret key
from config import Config  # import configuration values

# set up logging
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(Config.LOG_FILE)
file_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(file_handler)

# create a Binance exchange object using the API and secret keys
exchange = ccxt.binance({
    'apiKey': keys.API_KEY,
    'secret': keys.SECRET_KEY
})

# use the Binance testnet
exchange.set_sandbox_mode(True)

# get the latest ticker information for the trading symbol
ticker = exchange.fetch_ticker(Config.SYMBOL)

# lists to store the orders
buy_orders = []
sell_orders = []

# function to write the current order data to a JSON file
def write_order_log(new_data, side):
    with open(Config.ORDER_LOG, 'r+') as file:
        try:
            # load existing order data from the file
            file_data = json.load(file)
        except ValueError:
            # if the file is empty or invalid JSON, start with empty lists
            file_data = {
                'buy': [],
                'sell': []
            }

        # update the relevant list with the new data
        file_data[side] = new_data

        # overwrite the file with the updated order data
        file.seek(0)
        json.dump(file_data, file)

# function to create a limit buy order at the given price
def create_buy_order(symbol, size, price):
    logger.info("==> submitting market limit buy order at {}".format(price))
    order = exchange.create_limit_buy_order(symbol, size, price)
    buy_orders.append(order['info'])

# function to create a limit sell order at the given price
def create_sell_order(symbol, size, price):
    logger.info("==> submitting market limit sell order at {}".format(price))
    order = exchange.create_limit_sell_order(symbol, size, price)
    sell_orders.append(order['info'])

# function to read order data from the file (if it exists) and populate the buy_orders and sell_orders lists
def init():
    global buy_orders, sell_orders

    if os.path.exists(Config.ORDER_LOG):
        with open(Config.ORDER_LOG, 'r+') as file:
            file_data = json.load(file)
            buy_orders = file_data['buy']
            sell_orders = file_data['sell']
    else:
        # if the file doesn't exist, create an empty one
        open(Config.ORDER_LOG, 'a').close()

# main trading logic
def main():
    logger.info('=> Starting grid trading bot')

    global buy_orders, sell_orders
    
    if not buy_orders:
        # place inital buy orders
        for i in range(Config.NUM_BUY_GRID_LINES):
            price = ticker['bid'] - (Config.GRID_STEP_SIZE * (i + 1))
            create_buy_order(Config.SYMBOL, Config.POSITION_SIZE, price)
        
        # write order logs to file
        write_order_log(buy_orders, 'buy')

        # place initial sell orders
        for i in range(Config.NUM_SELL_GRID_LINES):
            price = ticker['bid'] + (Config.GRID_STEP_SIZE * (i + 1))
            create_sell_order(Config.SYMBOL, Config.POSITION_SIZE, price)

        # write order logs to file
        write_order_log(sell_orders, 'sell')

    while True:
        closed_order_ids = []

        # check if buy order is closed
        for buy_order in buy_orders:
            logger.info("=> checking buy order {}".format(buy_order['orderId']))
            try:
                order = exchange.fetch_order(buy_order['orderId'], Config.SYMBOL)
            except Exception as e:
                logger.error(e)
                logger.warning("=> request failed, retrying")
                continue
                
            order_info = order['info']

            if order_info['status'] == Config.FILLED_ORDER_STATUS:
                closed_order_ids.append(order_info['orderId'])
                logger.info("=> buy order executed at {}".format(order_info['price']))
                new_sell_price = float(order_info['price']) + Config.GRID_STEP_SIZE
                logger.info("=> creating new limit sell order at {}".format(new_sell_price))
                create_sell_order(Config.SYMBOL, Config.POSITION_SIZE, new_sell_price)

            time.sleep(Config.CHECK_ORDERS_FREQUENCY)

        # check if sell order is closed
        for sell_order in sell_orders:
            logger.info("=> checking sell order {}".format(sell_order['orderId']))
            try:
                order = exchange.fetch_order(sell_order['orderId'], Config.SYMBOL)
            except Exception as e:
                logger.error(e)
                logger.warning("=> request failed, retrying")
                continue
                
            order_info = order['info']

            if order_info['status'] == Config.FILLED_ORDER_STATUS:
                closed_order_ids.append(order_info['orderId'])
                logger.info("=> sell order executed at {}".format(order_info['price']))
                new_buy_price = float(order_info['price']) - Config.GRID_STEP_SIZE
                logger.info("=> creating new limit buy order at {}".format(new_buy_price))
                create_buy_order(Config.SYMBOL, Config.POSITION_SIZE, new_buy_price)

            time.sleep(Config.CHECK_ORDERS_FREQUENCY)

        # remove closed orders from list
        buy_orders = [buy_order for buy_order in buy_orders if buy_order['orderId'] not in closed_order_ids]
        sell_orders = [sell_order for sell_order in sell_orders if sell_order['orderId'] not in closed_order_ids]
        
        if closed_order_ids:
            # write updated order logs to file
            write_order_log(buy_orders, 'buy')
            write_order_log(sell_orders, 'sell')

        # exit if no sell orders are left
        if len(sell_orders) == 0:
            sys.exit("stopping bot, nothing left to sell")

if __name__ == "__main__":
    init()
    main()