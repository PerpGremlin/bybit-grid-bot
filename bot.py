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