import asyncio
from scanner import Scanner
from alerts import AlertManager
import schedule
import time
from datetime import datetime

def run_scanner():
    """Function to run the scanner for both timeframes."""
    async def main():
        alert_manager = AlertManager()
        scanner = Scanner(alert_manager)

        # Run for 5m timeframe
        scanner.run_scan('5m')

        # Run for 1h timeframe
        scanner.run_scan('1h')

        # Send any alerts found
        await alert_manager.send_batch()

    asyncio.run(main())

def main_app():
    """Main application loop."""
    print("Starting stock scanner...")

    # Schedule the scanner to run every 5 minutes
    schedule.every(5).minutes.do(run_scanner)

    # Run the scheduler
    while True:
        # Check if within market hours (9:15 AM to 3:30 PM IST)
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        if market_open <= now <= market_close and now.weekday() < 5: # Monday to Friday
            schedule.run_pending()

        time.sleep(1)

if __name__ == "__main__":
    main_app()
