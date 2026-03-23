# ==============================================================
# bot.py    - connection test
# purpose:  verify that our API keys work and that we can talk 
#           to bybit's testnet servers successfully
# author:   perpgremlin-
# date:     march 2026
#==============================================================

# pybit is the official bybit python library
# HTTP is the class we use for standard api requests (not websocket) 

from pybit.unified_trading import HTTP

# dotenv lets us load avriables from our .env file
# this keeps our api keys out of the code itself

from dotenv import load_dotenv

# os lets us read environmenmt variables once they're loaded

import os

# --- load api keys --- 
# this reads the .env file and loads its content into the environment
# so os.getenv() can access them below

load_dotenv() 

# --- create bybit session ---

# HTTP() creates a connection session to bybit's api
# testnet=True means that we are connecting to the fake money
# environment at testnet.bybit.com, not real bybit
# api_key and api_secret are pulled from the .env file - 
# os.getenv() looks up variable name and returns its value

session = HTTP(
    testnet=True,
    api_key=os.getenv("BYBIT_API_KEY"),         # your public api key  
    api_secret=os.getenv("BYBIT_API_SECRET")    # your private secret - never share
)

# --- make a test request --- 

# get_tickers() asks bybit for current market data 
# cagetory="spot" means the spot market (not futures or perps)
# symbol="BTCUSDT" is the trading pair we're asking about
#this is a read-only request - it doesn't place any orders

response = session.get_tickers(
    category="spot",
    symbol="BTCUSDT"
)

# --- print the result --- 

# print the raw response so we can see what bybit sent back
# if this shows price date, our connection is working 
# if this shows an error, something is wrong with the keys

print(response)