import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Construct path to .env file
script_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(script_dir, '.env')

# Load environment variables from .env file
load_dotenv(dotenv_path=dotenv_path)

class AlertManager:
    def __init__(self):
        """Initializes the AlertManager, loading credentials from environment variables."""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        self.daily_alert_count = 0
        self.max_daily_alerts = 10
        self.alert_cooldowns = {}  # {symbol: timestamp}
        self.cooldown_period = timedelta(minutes=30)
        self.alert_batch = []

    def is_on_cooldown(self, symbol):
        """Checks if a symbol is on cooldown."""
        if symbol in self.alert_cooldowns:
            if datetime.now() - self.alert_cooldowns[symbol] < self.cooldown_period:
                print(f"Symbol {symbol} is on cooldown.")
                return True
        return False

    def format_alert(self, alert_data):
        """Formats an alert message with all required details using HTML."""
        setup_type = alert_data['setup_type']
        symbol = alert_data['symbol']
        timeframe = alert_data['timeframe']
        score = alert_data['score']
        close_price = alert_data['close_price']
        ema_bounced = alert_data['ema_bounced']
        rsi = alert_data['rsi']
        volume_ratio = alert_data['volume_ratio']
        atr = alert_data['atr']

        if setup_type == 'bullish':
            emoji = "🚀"
            trade_type = "<b>EMA Stack Surge</b>"
            action = "Buy ATM Call"
            sl_price = close_price - (atr * 1.5)
            trail_sl_info = f"Trail SL below 9 EMA (5-min) or 21 EMA (1-hr)."
            exit_signal = "Exit if MACD crosses down or RSI > 70"
        else:  # Bearish
            emoji = "🐻"
            trade_type = "<b>Bearish Rejection</b>"
            action = "Buy ATM Put"
            sl_price = close_price + (atr * 1.5)
            trail_sl_info = f"Trail SL above 9 EMA (5-min) or 21 EMA (1-hr)."
            exit_signal = "Exit if MACD crosses up or RSI < 30"

        message = (
            f"{emoji} {trade_type}: {symbol} ({timeframe})\n"
            f"Bounced from <b>{ema_bounced} EMA</b> at ~{close_price:.2f}\n"
            f"Favor Score: <b>{score}/4</b>\n"
            f"Details: RSI({rsi:.1f}), Vol({volume_ratio:.1f}x Avg)\n"
            f"<b>Action:</b> {action}, Initial SL: <code>{sl_price:.2f}</code>\n"
            f"<i>Trailing SL: {trail_sl_info}</i>\n"
            f"<i>Exit Signal: {exit_signal}</i>"
        )
        return message

    def add_alert_to_batch(self, alert_data):
        """Checks cooldown, formats alert, and adds it to the batch."""
        symbol = alert_data['symbol']
        if self.is_on_cooldown(symbol):
            return False

        if self.daily_alert_count >= self.max_daily_alerts:
            print("Max daily alerts reached.")
            return False

        formatted_message = self.format_alert(alert_data)
        self.alert_batch.append(formatted_message)
        self.daily_alert_count += 1
        self.alert_cooldowns[symbol] = datetime.now()
        print(f"Alert for {symbol} added to batch. Daily count: {self.daily_alert_count}")
        return True

    def send_batch(self):
        """Sends the batch of alerts to Telegram using the requests library."""
        if not self.bot_token or not self.chat_id:
            print("⚠️ Telegram credentials not set. Please add to .env file:")
            print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
            print("TELEGRAM_CHAT_ID=your_chat_id_here")
            return

        if not self.alert_batch:
            return

        for i in range(0, len(self.alert_batch), 3):
            chunk = self.alert_batch[i:i+3]
            message = "\n\n---\n\n".join(chunk)

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            try:
                response = requests.post(url, data=data)
                if response.status_code == 200:
                    print(f"✅ Alert batch of {len(chunk)} sent to Telegram")
                else:
                    print(f"❌ Failed to send alert: {response.text}")
            except Exception as e:
                print(f"❌ Telegram error: {e}")

        self.alert_batch = [] # Clear the batch

    def reset_daily_count(self):
        """Resets the daily alert count."""
        self.daily_alert_count = 0

if __name__ == '__main__':
    # Test the refactored AlertManager

    # Create a dummy .env file for testing if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("TELEGRAM_BOT_TOKEN=your_token\n")
            f.write("TELEGRAM_CHAT_ID=your_chat_id\n")

    alert_manager = AlertManager()

    # Dummy alert data
    bullish_alert = {
        'setup_type': 'bullish', 'symbol': 'RELIANCE.NS', 'timeframe': '5m',
        'score': 4, 'close_price': 2950.50, 'ema_bounced': 9,
        'rsi': 58.2, 'volume_ratio': 1.8, 'atr': 25.5
    }
    bearish_alert = {
        'setup_type': 'bearish', 'symbol': 'TCS.NS', 'timeframe': '1h',
        'score': 3, 'close_price': 3800.00, 'ema_bounced': 5,
        'rsi': 42.1, 'volume_ratio': 1.3, 'atr': 40.0
    }

    # Test adding alerts
    alert_manager.add_alert_to_batch(bullish_alert)
    alert_manager.add_alert_to_batch(bearish_alert)

    # Test cooldown
    alert_manager.add_alert_to_batch(bullish_alert) # Should be on cooldown

    print(f"Alerts in batch: {len(alert_manager.alert_batch)}")

    # Test sending
    alert_manager.send_batch()
    print("Batch sent.")

    # Clean up dummy .env file
    if "your_token" in alert_manager.bot_token:
        os.remove('.env')
