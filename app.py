from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import threading
import time
from coin_scraper import CoinGeckoScraper
import pandas as pd
import plotly
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Use environment variable for secret key
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
scraper = CoinGeckoScraper(update_interval=60)
latest_data = {}
price_history = {}

def background_scraper():
    """Run the scraper in the background and emit updates via WebSocket."""
    while True:
        try:
            data = scraper.get_current_prices()
            if data:
                latest_data.update(data)
                # Update price history
                for coin in data:
                    if coin not in price_history:
                        price_history[coin] = []
                    price_history[coin].append({
                        'timestamp': time.time(),
                        'price': data[coin].get('usd', 0)
                    })
                    # Keep only last 100 data points
                    price_history[coin] = price_history[coin][-100:]
                
                # Emit update via WebSocket
                socketio.emit('price_update', {
                    'latest_data': latest_data,
                    'price_history': price_history
                })
        except Exception as e:
            app.logger.error(f"Error in background scraper: {str(e)}")
        time.sleep(60)  # Update every minute

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/latest')
def get_latest():
    """API endpoint to get latest price data."""
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    """API endpoint to get price history."""
    return jsonify(price_history)

@app.route('/api/chart/<coin>')
def get_chart(coin):
    """Generate price chart for a specific coin."""
    if coin in price_history:
        df = pd.DataFrame(price_history[coin])
        fig = {
            'data': [{
                'x': df['timestamp'],
                'y': df['price'],
                'type': 'scatter',
                'name': coin
            }],
            'layout': {
                'title': f'{coin.upper()} Price History',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Price (USD)'}
            }
        }
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return jsonify({'error': 'No data available'})

if __name__ == '__main__':
    # Start the background scraper thread
    scraper_thread = threading.Thread(target=background_scraper, daemon=True)
    scraper_thread.start()
    
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=port) 