import requests
import time
from datetime import datetime
import json
from typing import Dict, List, Optional
import sys
import csv
import os
import logging
from collections import deque
import statistics
from termcolor import colored
import yaml

class CoinGeckoScraper:
    def __init__(self, update_interval: int = 60):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.update_interval = update_interval
        self._setup_logging()
        self._load_config()
        
        # Initialize price history for technical indicators
        self.price_history = {coin: deque(maxlen=30) for coin in self.coins}
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('coin_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning("Config file not found. Creating default config.")
            config = self._create_default_config()
            
        self.coins = config['coins']
        self.currencies = config['currencies']
        self.csv_file = config['csv_file']
        self.price_alerts = config['price_alerts']
        self._setup_csv()
        
    def _create_default_config(self) -> Dict:
        """Create default configuration."""
        config = {
            'coins': [
                "bitcoin", "ethereum", "binancecoin", "ripple", "cardano",
                "solana", "polkadot", "dogecoin", "avalanche-2", "polygon",
                "chainlink", "uniswap", "aave", "stellar", "cosmos", "monero"
            ],
            'currencies': ["usd", "eur", "gbp"],
            'csv_file': "coin_prices.csv",
            'price_alerts': {
                "bitcoin": {"high": 85000, "low": 80000},
                "ethereum": {"high": 2000, "low": 1800}
            }
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        return config
        
    def _setup_csv(self):
        """Setup CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_file):
            headers = [
                "timestamp", "coin", "price_usd", "price_eur", "price_gbp",
                "change_24h", "volume_24h", "market_cap", "rsi", "ma_7", "ma_30"
            ]
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI for a list of prices."""
        if len(prices) < period + 1:
            return None
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = statistics.mean(gains[-period:])
        avg_loss = statistics.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def calculate_moving_average(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate moving average for a list of prices."""
        if len(prices) < period:
            return None
        return statistics.mean(prices[-period:])
        
    def check_price_alerts(self, coin: str, price: float):
        """Check if price alerts should be triggered."""
        if coin in self.price_alerts:
            alerts = self.price_alerts[coin]
            if price >= alerts.get('high', float('inf')):
                self.logger.warning(f"ALERT: {coin} price ({price}) is above {alerts['high']}")
            if price <= alerts.get('low', float('-inf')):
                self.logger.warning(f"ALERT: {coin} price ({price}) is below {alerts['low']}")
                
    def get_current_prices(self) -> Dict:
        """Fetch current prices for tracked coins."""
        try:
            # Implement rate limiting
            time.sleep(1)  # Basic rate limiting
            
            coin_ids = ",".join(self.coins)
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": coin_ids,
                "vs_currencies": ",".join(self.currencies),
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching prices: {e}")
            return {}

    def save_to_csv(self, data: Dict):
        """Save price data to CSV file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for coin in self.coins:
                if coin in data:
                    # Calculate technical indicators
                    rsi = self.calculate_rsi(list(self.price_history[coin]))
                    ma_7 = self.calculate_moving_average(list(self.price_history[coin]), 7)
                    ma_30 = self.calculate_moving_average(list(self.price_history[coin]), 30)
                    
                    row = [
                        timestamp,
                        coin,
                        data[coin].get("usd", "N/A"),
                        data[coin].get("eur", "N/A"),
                        data[coin].get("gbp", "N/A"),
                        data[coin].get("usd_24h_change", "N/A"),
                        data[coin].get("usd_24h_vol", "N/A"),
                        data[coin].get("usd_market_cap", "N/A"),
                        f"{rsi:.2f}" if rsi is not None else "N/A",
                        f"{ma_7:.2f}" if ma_7 is not None else "N/A",
                        f"{ma_30:.2f}" if ma_30 is not None else "N/A"
                    ]
                    writer.writerow(row)

    def display_prices(self, data: Dict):
        """Display current prices in a formatted way."""
        print("\n" + "="*120)
        print(f"Coin Prices - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*120)
        print(f"{'Coin':<15} {'Price (USD)':<12} {'Price (EUR)':<12} {'Price (GBP)':<12} "
              f"{'24h Change':<10} {'RSI':<8} {'MA(7)':<10} {'MA(30)':<10}")
        print("-"*120)
        
        for coin in self.coins:
            if coin in data:
                # Get prices in different currencies
                prices = {
                    "usd": data[coin].get("usd", "N/A"),
                    "eur": data[coin].get("eur", "N/A"),
                    "gbp": data[coin].get("gbp", "N/A")
                }
                
                # Update price history for technical indicators
                if isinstance(prices["usd"], (int, float)):
                    self.price_history[coin].append(prices["usd"])
                    self.check_price_alerts(coin, prices["usd"])
                
                # Calculate technical indicators
                rsi = self.calculate_rsi(list(self.price_history[coin]))
                ma_7 = self.calculate_moving_average(list(self.price_history[coin]), 7)
                ma_30 = self.calculate_moving_average(list(self.price_history[coin]), 30)
                
                # Format prices
                formatted_prices = {}
                for currency, price in prices.items():
                    if isinstance(price, (int, float)):
                        formatted_prices[currency] = f"${price:,.2f}" if currency == "usd" else f"€{price:,.2f}" if currency == "eur" else f"£{price:,.2f}"
                    else:
                        formatted_prices[currency] = "N/A"
                
                # Get other metrics
                change = data[coin].get("usd_24h_change", "N/A")
                
                # Format other metrics
                if isinstance(change, (int, float)):
                    change = f"{change:+.2f}%"
                    change_color = 'green' if change.startswith('+') else 'red'
                    change = colored(change, change_color)
                
                # Format technical indicators
                rsi_str = f"{rsi:.2f}" if rsi is not None else "N/A"
                ma_7_str = f"{ma_7:.2f}" if ma_7 is not None else "N/A"
                ma_30_str = f"{ma_30:.2f}" if ma_30 is not None else "N/A"
                
                print(f"{coin:<15} {formatted_prices['usd']:<12} {formatted_prices['eur']:<12} "
                      f"{formatted_prices['gbp']:<12} {change:<10} {rsi_str:<8} {ma_7_str:<10} {ma_30_str:<10}")
        
        print("="*120 + "\n")

    def run(self):
        """Run the scraper continuously."""
        self.logger.info("Starting CoinGecko Price Scraper...")
        print("Starting CoinGecko Price Scraper...")
        print("Press Ctrl+C to stop")
        print(f"Updating every {self.update_interval} seconds")
        print(f"Data will be saved to {self.csv_file}")
        print("Price alerts are active for configured coins")
        
        try:
            while True:
                data = self.get_current_prices()
                if data:
                    self.display_prices(data)
                    self.save_to_csv(data)
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping scraper...")
            print("\nStopping scraper...")
            sys.exit(0)

if __name__ == "__main__":
    # You can change the update interval here (in seconds)
    UPDATE_INTERVAL = 60
    scraper = CoinGeckoScraper(update_interval=UPDATE_INTERVAL)
    scraper.run() 