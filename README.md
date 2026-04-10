# Bybit Grid Bot

A fully automated, self-maintaining spot grid trading bot for Bybit.

## What it does

- Places a grid of buy and sell orders across a defined price range
- Automatically replaces filled orders to keep the grid full at all times
- Trails the grid when price approaches a boundary
- Monitors account balance as a circuit breaker
- Sends Telegram alerts for key events
- Shuts down cleanly, cancelling all orders on exit

## Features

- **Self-maintaining** — detects filled orders every loop and replaces them automatically
- **Trailing grid** — shifts the entire grid up or down when price moves near a boundary
- **Hard floor** — grid will never trail below a defined price level
- **Stop loss** — bot halts if account balance drops below a threshold
- **Telegram alerts** — startup, fills, trailing, stop loss, and shutdown notifications
- **Clean shutdown** — Ctrl+C cancels all open orders before exiting
- **Fully commented** — every line explained

## Requirements

- Python 3.12+
- Bybit account (testnet or live)
- A VPS or always-on machine for 24/7 operation

## Installation

```bash
# clone the repo
git clone git@github.com:PerpGremlin/bybit-grid-bot.git
cd bybit-grid-bot

# install dependencies
pip3 install -r requirements.txt --break-system-packages
```

## Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
nano .env
```

Your `.env` file should contain:

```
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Then edit `config.py` to set your trading parameters:

```python
SYMBOL = "BTCUSDT"          # trading pair
GRID_LOWER_PRICE = 54000.0  # bottom of grid range
GRID_UPPER_PRICE = 94000.0  # top of grid range
GRID_NUM_LEVELS = 10        # number of grid levels
GRID_ORDER_SIZE = 50.0      # USDT per order
```

## API Key Setup

When creating your Bybit API key:

- Enable **Read** and **Trade** permissions only
- **Disable Withdraw** — non-negotiable
- Whitelist your server IP address
- Never whitelist a home IP — home IPs are dynamic and change

## Running the bot

```bash
python3 bot.py
```

For 24/7 operation on a VPS, use screen:

```bash
screen -S gridbot
python3 bot.py
# detach with Ctrl+A then D
# reconnect with: screen -r gridbot
```

Stop the bot cleanly with `Ctrl+C` — this cancels all open orders before exiting.

## Security

- Never commit your `.env` file — it is blocked by `.gitignore`
- Store API keys in `.env` only — never hardcode them
- Use IP whitelisting on all API keys
- Disable withdraw on all API keys
- Run on testnet first — always

## Project structure

```
bybit-grid-bot/
    bot.py              — main bot logic
    config.py           — trading parameters
    .env                — API keys (never commit)
    .env.example        — safe template
    .gitignore          — protects sensitive files
    requirements.txt    — Python dependencies
    logs/               — bot activity logs
```

## Built with

- [pybit](https://github.com/bybit-exchange/pybit) — official Bybit Python SDK
- [python-dotenv](https://github.com/theskumar/python-dotenv) — environment variable management
- urllib — Telegram alerts (avoids conflict with pybit)

## Status

Currently paper trading on Bybit testnet.

---

*Built by perpgremlin-*
