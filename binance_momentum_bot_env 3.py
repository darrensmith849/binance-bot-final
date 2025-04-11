
import time
import os
import math
from binance.client import Client
from binance.enums import *

# STEP 1: Secure API key loading from environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)

# CONFIG
symbol = 'HBARUSDT'
max_positions = 5
investment_percent = 0.12  # 12% per trade
trailing_stop_percent = 0.02
moving_avg_period = 20
volume_threshold = 1.5
open_positions = {}

# Get current USDT balance
def get_portfolio_value():
    balance = client.get_asset_balance(asset='USDT')
    return float(balance['free'])

# Calculate how many units to buy
def calculate_quantity_to_buy(symbol, max_usdt):
    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    quantity = math.floor((max_usdt / price) * 100) / 100
    return quantity, price

# Main bot logic
def main():
    while True:
        try:
            if len(open_positions) >= max_positions:
                print("Max positions reached. Skipping new trades.")
                time.sleep(10)
                continue

            klines = client.get_klines(symbol=symbol, interval='1m', limit=100)
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            current_price = closes[-1]
            current_volume = volumes[-1]
            moving_avg = sum(closes[-moving_avg_period:]) / moving_avg_period
            avg_volume = sum(volumes[-moving_avg_period:]) / moving_avg_period

            if symbol not in open_positions and current_price > moving_avg and current_volume > avg_volume * volume_threshold:
                portfolio_value = get_portfolio_value()
                usdt_to_spend = portfolio_value * investment_percent
                quantity, actual_price = calculate_quantity_to_buy(symbol, usdt_to_spend)
                if quantity > 0:
                    order = client.order_market_buy(symbol=symbol, quantity=quantity)
                    open_positions[symbol] = {
                        'buy_price': actual_price,
                        'highest_price': actual_price
                    }
                    print(f"BOUGHT {quantity} {symbol} at {actual_price} | Portfolio: ${portfolio_value:.2f}")

            if symbol in open_positions:
                pos = open_positions[symbol]
                if current_price > pos['highest_price']:
                    pos['highest_price'] = current_price

                if current_price < pos['highest_price'] * (1 - trailing_stop_percent):
                    quantity, _ = calculate_quantity_to_buy(symbol, get_portfolio_value() * investment_percent)
                    order = client.order_market_sell(symbol=symbol, quantity=quantity)
                    print(f"SOLD {symbol} at {current_price}")
                    del open_positions[symbol]

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(10)

if __name__ == '__main__':
    main()
