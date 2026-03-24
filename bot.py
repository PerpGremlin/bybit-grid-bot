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
