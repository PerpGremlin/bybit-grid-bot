# ============================================================
# config.py - bot control panel
# purpose:  all trading settings live here in one place
#           adjust these values to change how the bot behaves
#           never hardcode these values directly in bot.py
# author:   perpgremlin-
# date:     march 2026
# ============================================================

# ---- trading pair -----------------------------------------

# which market to trade on 
# format is always BASE + QUOTE e.g BTC + USDT = BTCUSDT
SYMBOL = "BTCUSDT"

# market category
# 'spot'    = spot trading, you oown the actual coin
# 'linear'  = perpetual futures, USDT margined
# 'inverse' = perpetual futures, coin margined
# start with spot - safest for testing
CATEGORY = 'spot'

# ---- grid range -------------------------------------------

# the lowest price that your grid will reach
# bot places buy orders down to this level
# set this at a strong support level on your chart
GRID_LOWER_PRICE = 44000.0

# this is the highest price your grid will reach
# bot places sell orders up to this level
# set this as a strong resistance level on your chart
GRID_UPPER_PRICE = 84000.0

# how many grid lines to place between lower and upper
# more levels = smaller gaps = more frequent trades
# fewer levels = bigger gaps = larger profit per trade
# 10 is a good starting point for testing
GRID_NUM_LEVELS = 10

# ---- order sizing -----------------------------------------

# how much total USDT to use per grid order
# total capital at work = GRID_ORDER_SIZE x GRID_NUM_LEVELS
# e.g. 50 USDT x 10 levels = 500 USDT total 
# keep this small while testing on testnet
GRID_ORDER_SIZE = 50.0

# ---- safety settings --------------------------------------

# emergency stop - bot cancels all orders and halts
# if account balance drops below this number (in USDT)
# protects you in a strong trending market
# set this below your starting balance but above zero
STOP_LOSS_BALANCE = 800.0

# maximum number of open orders allowed at any time
# safety cap - prevents order spam if something breaks
MAX_OPEN_ORDERS = 20

# ---- timing -----------------------------------------------

# how many seconds between each market check
# 60 = bot checks prices and orders once per minute
# do not go below 10 - bybit has api rate limits
# lower values = more responsive but more API usage
LOOP_INTERVAL_SECONDS = 60

# ---- logging ----------------------------------------------

# where the bot writes its activity log file
# every order, price check and error gets recorded here
LOG_FILE = "logs/grid_bot.log"

# how much detail to log
# "INFO"    = normal operations, orders placed and filled
# "DEBUG"   = everything including raw API responses
# use DEBUG when troubleshooting, INFO for normal use
LOG_LEVEL = "INFO"

# ---- trailing grid settings -------------------------------

# whether the grid trails price or stays fixed
# True  = grid shifts when price moves past a boundary
# False = static grid, stays between set lower and upper price
TRAILING_ENABLED = True

# how far price must move past a grid level before
# the whole grid shifts in that direction
# expressed as a fraction of one grid interval
# 0.5       = price must move half a grid interval beyond the edge
# lower     = more sensitive, shifts more often
# higher    = less sensitive, shifts less often
TRAIL_TRIGGER = 0.5

# trail direction
# "both"    = grid follows price up and down
# "up"      = grid only trails upward, hard floor at lower price
# "down"    = grid only trails downward, hard ceiling at upper price
TRAIL_DIRECTION = "both"

# hard floor - if TRAIL_DIRECTION is "up", the grid will
# never trail below this price. acts as your absolute
# stop level based on your macro support analysis
TRAIL_HARD_FLOOR = 44000.0

# directional bias - ratio of buy orders to sell orders.
# 1.0 = perfectly neutral, equal buys and sells
# 1.5 = 50% more buy orders than sell orders (bullish lean)
# 0.5 = 50% more sell orders than buy orders (bearish lean)
# neutral is the sdafest while testing
ORDER_BIAS = 1.0

