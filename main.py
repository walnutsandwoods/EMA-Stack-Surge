from scanner import Scanner
from alerts import AlertManager
import schedule
import time
from datetime import datetime

def run_scan_job(scanner, alert_manager):
    """
    The job function that the scheduler will run.
    It runs the scans and sends a batch of alerts.
    """
    print("\\n--- New Scan Cycle ---")
    # Run for 5m timeframe
    scanner.run_scan('5m')

    # Run for 1h timeframe
    scanner.run_scan('1h')

    # Send any alerts found
    alert_manager.send_batch()
    print("--- Scan Cycle Complete ---")

def main_app():
    """Main application loop."""
    print("Starting stock scanner...")

    # Instantiate the core components once
    alert_manager = AlertManager()
    scanner = Scanner(alert_manager)

    print("Running initial scan...")
    run_scan_job(scanner, alert_manager)

    # Schedule the scanner to run every 5 minutes
    print("Scheduling scan job to run every 5 minutes...")
    schedule.every(5).minutes.do(run_scan_job, scanner=scanner, alert_manager=alert_manager)

    # Main loop to run the scheduler
    while True:
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        # Run scheduler only during market hours on weekdays
        if market_open <= now <= market_close and now.weekday() < 5:
            schedule.run_pending()
        else:
            # Optional: print a message when outside market hours
            current_time = now.strftime("%H:%M:%S")
            print(f"Market is closed. Current time: {current_time}. Waiting for market to open...", end="\\r")

        time.sleep(1)

if __name__ == "__main__":
    main_app()
