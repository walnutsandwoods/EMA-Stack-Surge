import pandas as pd
from utils import get_stock_list, get_stock_data, calculate_indicators
from alerts import AlertManager
import logging
from datetime import datetime
import os

# Setup logging to a file in the script's directory
script_dir = os.path.dirname(__file__)
log_file_path = os.path.join(script_dir, 'scan_log.csv')
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s,%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Scanner:
    def __init__(self, alert_manager):
        self.stock_list = get_stock_list()
        self.alert_manager = alert_manager

    def check_setup(self, df, timeframe, symbol):
        """Checks for bullish and bearish setups in the data."""
        if df.empty or len(df) < 21: # Ensure enough data for 20-period VMA
            return None

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # Indicators
        ema5 = latest['EMA_5']
        ema9 = latest['EMA_9']
        ema21 = latest['EMA_21']
        rsi = latest['RSI_7'] if timeframe == '5m' else latest['RSI_9']
        volume = latest['Volume']
        volume_ma = latest['VMA_20']
        macd_line = latest['MACD_12_26_9'] if timeframe == '5m' else latest['MACD_48_104_36']
        macd_hist = latest['MACDh_12_26_9'] if timeframe == '5m' else latest['MACDh_48_104_36']
        macd_signal = latest['MACDs_12_26_9'] if timeframe == '5m' else latest['MACDs_48_104_36']
        atr = latest['ATRr_14']

        # --- Bullish Setup Check ---
        # 1. Calculate all four boolean conditions
        ema_stack_bullish = ema5 > ema9 > ema21
        rsi_bullish = rsi > 50
        volume_surge_bullish = (volume > 1.5 * volume_ma) if timeframe == '5m' else (volume > 1.2 * volume_ma)
        macd_bullish = macd_line > macd_signal and macd_hist > 0

        # 2. Calculate the favor score
        favor_score_bullish = sum([ema_stack_bullish, rsi_bullish, volume_surge_bullish, macd_bullish])

        # 3. Check if the score is high enough
        if favor_score_bullish >= 3:
            # 4. If score is high enough, check for the price dip action
            for ema_period, ema_val in [(5, ema5), (9, ema9)]:
                price_dip_bullish = (previous['Low'] <= ema_val * 1.02) and (latest['Close'] > ema_val)
                if price_dip_bullish:
                    # All conditions met, generate alert
                    alert_data = {
                        'setup_type': 'bullish', 'symbol': symbol, 'timeframe': timeframe,
                        'score': favor_score_bullish, 'close_price': latest['Close'], 'ema_bounced': ema_period,
                        'rsi': rsi, 'volume_ratio': volume / volume_ma if volume_ma > 0 else 0, 'atr': atr,
                        'ema5': ema5
                    }
                    logging.info(f"{symbol},{timeframe},bullish,{latest['Close']},{favor_score_bullish}")
                    return alert_data

        # --- Bearish Setup Check ---
        # 1. Calculate all four boolean conditions
        ema_stack_bearish = ema5 < ema9 < ema21
        rsi_bearish = rsi < 50
        volume_surge_bearish = (volume > 1.5 * volume_ma) if timeframe == '5m' else (volume > 1.2 * volume_ma)
        macd_bearish = macd_line < macd_signal and macd_hist < 0

        # 2. Calculate the favor score
        favor_score_bearish = sum([ema_stack_bearish, rsi_bearish, volume_surge_bearish, macd_bearish])

        # 3. Check if the score is high enough
        if favor_score_bearish >= 3:
            # 4. If score is high enough, check for the price rally action
            for ema_period, ema_val in [(5, ema5), (9, ema9)]:
                price_rally_bearish = (previous['High'] >= ema_val * 0.98) and (latest['Close'] < ema_val)
                if price_rally_bearish:
                    # All conditions met, generate alert
                    alert_data = {
                        'setup_type': 'bearish', 'symbol': symbol, 'timeframe': timeframe,
                        'score': favor_score_bearish, 'close_price': latest['Close'], 'ema_bounced': ema_period,
                        'rsi': rsi, 'volume_ratio': volume / volume_ma if volume_ma > 0 else 0, 'atr': atr,
                        'ema5': ema5
                    }
                    logging.info(f"{symbol},{timeframe},bearish,{latest['Close']},{favor_score_bearish}")
                    return alert_data

        return None

    def run_scan(self, timeframe):
        """Runs the scanner for a given timeframe."""
        print(f"Running {timeframe} scan at {datetime.now()}...")
        period = '5d' if timeframe == '5m' else '60d'

        for stock in self.stock_list:
            if self.alert_manager.daily_alert_count >= self.alert_manager.max_daily_alerts:
                print("Max daily alerts reached. Halting scan for this cycle.")
                break

            # Cooldown check is now handled by the AlertManager
            try:
                data = get_stock_data(stock, interval=timeframe, period=period)
                if not data.empty:
                    data_with_indicators = calculate_indicators(data.copy(), timeframe)
                    alert_data = self.check_setup(data_with_indicators, timeframe, stock)
                    if alert_data:
                        if alert_data['setup_type'] == 'bearish':
                            print(f"[DEBUG] Bearish setup found for {stock}. Passing to AlertManager.")
                        self.alert_manager.add_alert_to_batch(alert_data)

            except Exception as e:
                print(f"Error processing {stock}: {e}")
                continue

# This file is not intended to be run directly.
# Please use main.py as the entry point.
