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