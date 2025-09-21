import configparser
import telegram
from datetime import datetime, timedelta

class AlertManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.bot_token = self.config['telegram']['bot_token']
        self.chat_id = self.config['telegram']['chat_id']
        self.bot = telegram.Bot(token=self.bot_token)

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
        """Formats an alert message with all required details."""
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
            trade_type = "Bullish Bounce"
            action = "Buy ATM Call"
            sl_price = close_price - (atr * 1.5)
            trail_sl_info = f"Trail SL below 9 EMA (5-min) or 21 EMA (1-hr)."
            exit_signal = "Exit if MACD crosses down or RSI > 70"
        else:  # Bearish
            emoji = "🐻"
            trade_type = "Bearish Rejection"
            action = "Buy ATM Put"
            sl_price = close_price + (atr * 1.5)
            trail_sl_info = f"Trail SL above 9 EMA (5-min) or 21 EMA (1-hr)."
            exit_signal = "Exit if MACD crosses up or RSI < 30"

        message = (
            f"{emoji} {trade_type}: {symbol} ({timeframe})\\n"
            f"Bounced from {ema_bounced} EMA at ~{close_price:.2f}\\n"
            f"Favor Score: {score}/4\\n"
            f"Details: RSI({rsi:.1f}), Vol({volume_ratio:.1f}x Avg)\\n"
            f"Action: {action}, Initial SL: {sl_price:.2f}\\n"
            f"Trailing SL: {trail_sl_info}\\n"
            f"Exit Signal: {exit_signal}"
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

    async def send_batch(self):
        """Sends the batch of alerts."""
        if not self.alert_batch:
            return

        for i in range(0, len(self.alert_batch), 3):
            chunk = self.alert_batch[i:i+3]
            message = "\\n\\n---\\n\\n".join(chunk)
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=message)
                print(f"Sent batch of {len(chunk)} alerts.")
            except Exception as e:
                print(f"Error sending Telegram message: {e}")

        self.alert_batch = []

    def reset_daily_count(self):
        """Resets the daily alert count."""
        self.daily_alert_count = 0

if __name__ == '__main__':
    # Test the refactored AlertManager
    async def main():
        try:
            alert_manager = AlertManager()
        except (configparser.NoSectionError, KeyError):
            print("Please set up config.ini with your Telegram bot token and chat ID.")
            return

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
        await alert_manager.send_batch()
        print("Batch sent.")

    import asyncio
    asyncio.run(main())
