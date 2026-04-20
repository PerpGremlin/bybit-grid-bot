# ==============================================================
# bot.py    - bybit grid bot
# purpose:  automatically places and manages a grid of buy 
#           sell orders on bybit, without optional trailing
# author:   perpgremlin-
# date:     march 2026
#==============================================================


# ---- imports ----------------------------------------------

# pybit handles all communication with bybit's api
# HTTP is used for standard request/response calls 
from pybit.unified_trading import HTTP

# urllib is used for sending telegram alerts
# we use urllib instead of requests because requests
# conflicts with the pybit library
import urllib.request
import urllib.parse

# dotenv loads our .env file so python can read our api keys 
from dotenv import load_dotenv

# os lets us read environment variables like api keys
import os

# time lets us pause the bot between loops
# without this the bot would hammer bybit's api constantly
import time

# logging writes the bot's activity to a file
# so we can see exactlly what happened and when
import logging

# math gives us tools for rounding prices to valid levels
# bybit rejects orders with too many decimal places
import math

# config id our own file - imports all our trading strategies
# this is how bot.py reads everything from config.py
import config


# ---- telegram alert function ------------------------------

def send_telegram(message):
    # sends us a message to the telegram group chat
    # uses urllib to avoid conflicts with pybit
    # if telegram fails we log the error but never crash the bot
    try:
        # load telegram credentials from .env
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # if credentials are missing skip silently
        # lets the bot run without telegram if needed
        if not bot_token or not chat_id:
            logger.warning("telegram credentials not found - skipping alert")
            return

        # build the telegram api url
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # encode the message data
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": f"🤖 Grid Bot\n{message}",
            "parse_mode": "HTML"
        }).encode("utf-8")

        # send the request with a 10 second timeout
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        logger.info(f"telegram alert sent: {message}")

    except Exception as e:
        # never let a telegram failure crash the bot
        logger.error(f"telegram alert failed: {e}")


# ---- logging setup ----------------------------------------

# configure the logging system
# this sets up the bots activity diary
# every important event gets written to a file with a timestamp
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        # write logs to the file defined in config.py
        logging.FileHandler(config.LOG_FILE),
        # also print logs to the terminal so you can watch live
        logging.StreamHandler()
    ]
)
os.environ['PYTHONUNBUFFERED'] = '1'

# force logs to print immediately without buffering
# loggin.getLogger().handlers[1].flush = lambda: None
# import sys
# sys.stdout.reconfigure(line_buffering=True)

# create the logger objects
# we use this throughout the bot to write log messages
# e.g. logger.info("order placed") or logger.error("connection failed")
logger = logging.getLogger(__name__)                                  

# write the first log entry so we know the bot started
logger.info("=== grid bot starting up ===")
logger.info(f"symbol: {config.SYMBOL} | category: {config.CATEGORY}")
logger.info(f"grid range: {config.GRID_LOWER_PRICE} - {config.GRID_UPPER_PRICE}")
logger.info(f"grid levels:{config.GRID_NUM_LEVELS} | order size: {config.GRID_ORDER_SIZE} USDT")
logger.info(f"trailing enabled: {config.TRAILING_ENABLED} | direction: {config.TRAIL_DIRECTION}")


# ---- load api keys and connect to bybit ------------------

# load the .env file so python can read our api keys
# this must be called before any os.getenv() calls
load_dotenv()

# read the api keys from environment variables
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

# safely check - if keys are missing, stop immediately
# better to crash here than run with no authentication
if not API_KEY or not API_SECRET:
    logger.error("api keys not found in .env file - bot cannot start")
    raise SystemExit("missing api keys - check your .env file")

# create the bybit session
# this is the bot's phone line to bybit's servers
# testnet=True means we connect to fake money environment
# when live trading, change testnet=False
session = HTTP(
    testnet=True,
    api_key=API_KEY,
    api_secret=API_SECRET
)

logger.info("bybit session created successfully")
logger.info(f"testnet mode: {os.getenv('BYBIT_TESTNET', 'true')}")


# ---- grid calculation functions ---------------------------

def calculate_grid_levels(lower, upper, num_levels):
    # calculate the price gap between each grid level
    # e.g. range 44000-84000 with 10 levels = 4000 per level
    interval = (upper - lower) / num_levels

    # build a list of all price levels from bottom to top
    # each level is lower price + (interval * step number)
    levels = []
    for i in range(num_levels + 1):
        price = lower + (interval * i)
        # round to 1 decimal place - bybit rejects too many decimals
        price = round(price, 1)
        levels.append(price)

    return levels, interval


def get_buy_sell_levels(levels, current_price):
    # split levels into buys and sells based on current price
    # buy orders go below the current price
    # sell orders go above the current price
    buy_levels = [p for p in levels if p < current_price]
    sell_levels = [p for p in levels if p > current_price]

    return buy_levels, sell_levels


def get_current_price():
    # ask bybit for the current market price
    # this is a read only request - no orders placed
    try: 
        response = session.get_tickers(
            category=config.CATEGORY,
            symbol=config.SYMBOL
        )
        # extract the last traded price from the response
        price = float(response['result']['list'][0]['lastPrice'])
        logger.info(f"currentprice: {price}")
        return price
    except Exception as e:
        # if the request fails, log the error and return None
        logger.error(f"failed to get price: {e}")
        return None


# test the grid calculation on startup so we can see the levels
current_price = get_current_price()

if current_price:
    levels, interval = calculate_grid_levels(
        config.GRID_LOWER_PRICE,
        config.GRID_UPPER_PRICE,
        config.GRID_NUM_LEVELS
    )
    buy_levels, sell_levels = get_buy_sell_levels(levels, current_price)

    logger.info(f"grid interval: {interval} USDT per level")
    logger.info(f"total levels: {len(levels)}")
    logger.info(f"buy levels: {buy_levels}")
    logger.info(f"sell levels: {sell_levels}")


# ---- order placement functions ----------------------------
# ---- function displaying all asset balances ------

def get_account_balance():
   # ask bybit for all assets in the unified trading account
   # displays any asset with a USD value over $1
   # returns USDT balance for the stop loss check
   try:
       response = session.get_wallet_balance(
           accountType="UNIFIED"
       )
       # get the coin list from the response
       coin_list = response['result']['list'][0]['coin']

       # if coin list is empty, no funds in unified account
       if not coin_list:
           logger.warning("no funds found in unified account")
           return None

       # log total account equity first
       total_equity = response['result']['list'][0]['totalEquity']
       logger.info(f"total account equity: ${float(total_equity):,.2f}")
       logger.info("--- assets with value over $1 ---")

       # loop through all coins and display those worth over $1
       usdt_balance = None
       for coin in coin_list:
           usd_value = float(coin['usdValue'])
           if usd_value > 1:
               wallet_balance = float(coin['walletBalance'])
               coin_name = coin['coin']
               logger.info(f"{coin_name}: {wallet_balance} (${usd_value:,.2f})")
               # save USDT balance separately for stop loss check
               if coin_name == 'USDT':
                   usdt_balance = wallet_balance

       logger.info("--- end of assets ---")
       return float(total_equity)

   except Exception as e:
       logger.error(f"failed to get balance: {e}")
       return None

def place_order(side, price, qty):
    # place a single limit order on bybit
    # side = "Buy" or "Sell"
    # price = the price level to place the order at
    # qty = how much to buy or sell (in base currency e.g. BTC)
    try:
        response = session.place_order(
            category=config.CATEGORY,
            symbol=config.SYMBOL,
            side=side,
            orderType="Limit",
            price=str(price),
            qty=str(qty), 
            timeInForce="GTC"
        )
        # GTC means Godd Till Cancelled - order stays open
        # until it fills or we manually cancel it
        if response['retCode'] == 0:
            order_id = response['result']['orderId']
            logger.info(f"order placed: {side} {qty} BTC at {price} | id: {order_id}]")
            return order_id
        else:
            logger.error(f"order failed: {response['retMsg']}")
            return None
    except Exception as e:
        logger.error(f"order placement error: {e}")
        return None


def cancel_order(order_id):
    # cancel a single open order by its id
    try:
        response = session.cancel_order(
            category=config.CATEGORY,
            symbol=config.SYMBOL,
            orderId=order_id
        )
        if response['retCode'] == 0:
            logger.info(f"order cancelled: {order_id}")
            return True
        else:
            logger.error(f"cancel failed: {response['retMsg']}")
            return False
    except Exception as e:
        logger.error(f"cancel error: {e}")
        return False


def cancel_all_orders():
    # cancel every open order on this symbol
    # used when bot shuts down or grid shifts
    try:
        response = session.cancel_all_orders(
            category=config.CATEGORY, 
            symbol=config.SYMBOL
        )
        if response['retCode'] == 0:
            logger.info("all orders cancelled successfully")
            return True
        else:
            logger.error(f"cancel all failed: {response['retMsg']}")
            return False
    except Exception as e:
        logger.error(f"cancel all error: {e}")
        return False

def get_open_orders():
    # ask bybit for all currently open orders on this symbol
    # returns a list of dicts with price and side for each open order
    # we use this to compare against our grid levels each loop
    try:
        response = session.get_open_orders(
            category=config.CATEGORY,
            symbol=config.SYMBOL
        )

        if response['retCode'] == 0:
            orders = response['result']['list']
            logger.info(f"open orders on exchange: {len(orders)}")
            return orders
        else:
            logger.error(f"failed to get open orders: {response['retMsg']}")
            return []
    except Exception as e:
        logger.error(f"failed to get open orders: {e}")
        return []

def check_and_replenish(grid_levels, interval):
    # compare open orders against our grid levels
    # find any levels where the order has filled and is missing
    # place the correct replacement order at that level
    # includes a check to avoid placing duplicates

    # get all currently open orders from bybit
    open_orders = get_open_orders()

    # extract the prices of all open orders into a set
    # rounded to 1 decimal to match our grid level format
    open_prices = set()
    for order in open_orders:
        open_prices.add(round(float(order['price']), 1))

    # get current price so we know which side of the market we are on
    current_price = get_current_price()
    if not current_price:
        logger.warning("could not get price for replenishment check - skipping")
        return

    # check each grid level to see if it has an open order
    replenished = 0
    for level in grid_levels:
        level = round(level, 1)

        # if this level has an open order - nothing to do, move on
        if level in open_prices:
            continue

        # this level has no open order - it must be filled
        # work out what filled and what to place as replacement
        if level < current_price:
            # this was a buy order that filled
            # place a sell one interval above it to take profit
            sell_price = round(level + interval, 1)
            
            # only place if sell price is not already in open orders
            if sell_price not in open_prices:
                qty = calculate_order_qty(sell_price)
                logger.info(f"buy filled at {level} - placing sell at {sell_price}")
                order_id = place_order("Sell", sell_price, qty)
                if order_id:
                    open_prices.add(sell_price)
                    replenished += 1
                    send_telegram(f"buy filled at {level} - sell placed at {sell_price}")
                time.sleep(0.2)

        elif level > current_price:
            # this was a sell order that filled
            # place a buy order one interval below it to reload
            buy_price = round(level - interval, 1)

            # only place if buy ptice is not already in open orders
            if buy_price not in open_prices:
                qty = calculate_order_qty(buy_price)
                logger.info(f"sell filled at {level} - placing buy at {buy_price}")
                order_id = place_order("Buy", buy_price, qty)
                if order_id:
                    open_prices.add(buy_price)
                    replenished += 1        
                    send_telegram(f"sell filled at {level} - placing buy at {buy_price}")
                time.sleep(0.2)

    if replenished > 0:
        logger.info(f"replenished {replenished} orders this loop")


def calculate_order_qty(price):
# calculate how many BTC to buy/sell at a given price
# we want to spend GRID_ORDER_SIZE USDT per order
# so qty = USDT amount / price
# round to 6 decimal places - bybit minimum precision for BTC
    qty = round(config.GRID_ORDER_SIZE / price, 6)
    return qty


def place_grid_orders(buy_levels, sell_levels):
    # place all buy and sell orders for the current grid
    # returns a list of all order ids so we can track them
    order_ids = []

    # place buy orders at each level below current price
    for price in buy_levels:
        qty = calculate_order_qty(price)
        order_id = place_order("Buy", price, qty)
        if order_id:
            order_ids.append(order_id)
        # small pause between orders at each level to respect api rate limits
        time.sleep(0.2)

    # place sell orders at each level above current price
    for price in sell_levels:
        qty = calculate_order_qty(price)
        order_id = place_order("Sell", price, qty)
        if order_id:
            order_ids.append(order_id)
        time.sleep(0.2)

    logger.info(f"grid placed: {len(order_ids)} orders total")
    return order_ids


# test balance check on startup
balance = get_account_balance()

if balance and balance < config.STOP_LOSS_BALANCE:
    logger.warning(f"balance {balance} is below stopp loss {config.STOP_LOSS_BALANCE}")


# ---- main loop --------------------------------------------

def run_bot():
    # this is the main function that runs the bot forever
    # it loops contionuously until stopped with ctrl+c
    logger.info("=== starting main loop ===")
    send_telegram(f"=== grid bot started ===\ngrid: {config.GRID_LOWER_PRICE} - {config.GRID_UPPER_PRICE}\ntestnet: {os.getenv('BYBIT_TESTNET', 'true')}")

    # place the initial grid of orders on startup
    logger.info("placing initial grid orders...")
    current_price = get_current_price()

    if not current_price:
        logger.error("could not get price - cannot start bot")
        return

    # calculate and place the first grid
    levels, interval = calculate_grid_levels(
        config.GRID_LOWER_PRICE,
        config.GRID_UPPER_PRICE,
        config.GRID_NUM_LEVELS
    )
    buy_levels, sell_levels = get_buy_sell_levels(levels, current_price)
    active_order_ids = place_grid_orders(buy_levels, sell_levels)
    logger.info(f"initial grid placed with {len(active_order_ids)} orders")
    send_telegram(f"initial grid placed - {len(active_order_ids)} orders active")

    # store current grid boundaries so we can detect when
    # price moves outside them and the grid needs to trail
    grid_lower = config.GRID_LOWER_PRICE
    grid_upper = config.GRID_UPPER_PRICE

    # main loops runs forever until stopped
    while True:
        try:
            # wait for the configures interval before checking
            # this prevents hammering bybit's api
            logger.info(f"sleeping {config.LOOP_INTERVAL_SECONDS} seconds...")
            time.sleep(config.LOOP_INTERVAL_SECONDS)

            # --- check current price ---
            current_price = get_current_price()
            if not current_price:
                logger.warning("could not get price this loop - skipping")
                continue

            # --- check if trailing is needed FIRST ---
            # trailing must run before replenishment
            # so the grids shift before we check for missing orders
            if config.TRAILING_ENABLED:
                # calculate how far price has moved past grid edge
                trail_distance = interval * config.TRAIL_TRIGGER

                # check if price has moved above the upper boundary
                if current_price > grid_upper - trail_distance:
                    if config.TRAIL_DIRECTION in ["both", "up"]:
                        logger.info("price near upper boundary - trailing grid up")
                        send_telegram(f"trailing grid UP - new range {grid_lower + interval} - {grid_upper + interval}")
                        # shift grid up by one interval
                        grid_lower = grid_lower + interval
                        grid_upper = grid_upper + interval
                        logger.info(f"new grid range: {grid_lower} - {grid_upper}")
                        # cancel existing orders and place a new grid
                        cancel_all_orders()
                        levels, interval = calculate_grid_levels(
                            grid_lower, grid_upper, config.GRID_NUM_LEVELS
                        )
                        buy_levels, sell_levels = get_buy_sell_levels(
                            levels, current_price
                        )
                        active_order_ids = place_grid_orders(
                            buy_levels, sell_levels
                        )

                # check if price has moved below the lower boundary
                elif current_price < grid_lower + trail_distance:
                    if config.TRAIL_DIRECTION in ["both", "down"]:
                        # respect the hard floor setting
                        if grid_lower - interval >= config.TRAIL_HARD_FLOOR:
                            logger.info("price near lower boundary - trailing grid down")
                            grid_lower = grid_lower - interval
                            grid_upper = grid_upper - interval
                            send_telegram(f"grid trailing DOWN - new range: {grid_lower} - {grid_upper}")
                            cancel_all_orders()
                            levels, interval = calculate_grid_levels(
                                grid_lower, grid_upper, config.GRID_NUM_LEVELS
                            )
                            buy_levels, sell_levels = get_buy_sell_levels(
                                levels, current_price
                            )
                            active_order_ids = place_grid_orders(
                                buy_levels, sell_levels
                            )
                        else:
                            logger.warning(f"hard floor reached at {config.TRAIL_HARD_FLOOR} - not trailing down")

            # --- check and replenish filled orders AFTER trailing --- 
            # uses updated levels if grid just shifted
            check_and_replenish(levels, interval)

            # --- check account balance ---
            balance = get_account_balance()
            if balance and balance < config.STOP_LOSS_BALANCE:
                logger.error(f"balance {balance} below stop loss {config.STOP_LOSS_BALANCE} - shutting down")
                send_telegram(f"⚠️ STOP LOSS HIT — balance {balance} USDT — shutting down")
                cancel_all_orders()
                return

        except SystemExit:
            raise
        except Exception as e:
            # if anything unexpected happens, log it and keep running
            # we never want the bot to crash silently
            logger.error(f"error in main loop: {e}")
            logger.info("continuing despite error...")
            continue


# ---- shutdown handler -------------------------------------

import signal

def handle_shutdown(signum, frame):
    # this function runs when the bot receives a stop signal
    # signum is the signal number (e.g. ctrl+c = signal 2)
    # frame is the current stack frame - we dont use it
    logger.info("=== shutdown signal received ===")
    logger.info("cancelling all open orders before exiting...")

    # cancel everything on the exchange before wee leave
    # this prevents orphan orders sitting on bybit unmanaged
    cancel_all_orders()

    logger.info("all orders cancelled - bot stopped cleanly")
    send_telegram("bot stopped cleanly — all orders cancelled")
    logger.info("=== grid bot shutdown complete ===")

    # exit with 0 code means clean exit, no errors
    raise SystemExit(0)


# register the shutdown handler for these two signals
# SIGINT = ctrl+c from the keyboard
# SIGTERM = kill command from the operating system
# both will now trigger a clean shutdown instead of crashing
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# only run the bot if this file is run directly
# this prevents the bot starting if bot.py is imported elsewhere
if __name__ == "__main__":
    logger.info("shutdown handler registered - press ctrl+c to stop cleanly")
    run_bot()
