# Crypto Dashboard

A real-time cryptocurrency price tracking dashboard with technical indicators and price alerts.

## Features

- Real-time price updates
- Interactive price charts
- Technical indicators (RSI, Moving Averages)
- Price alerts
- Mobile-responsive design
- WebSocket support for live updates

## Deployment Options

### Option 1: Heroku (Recommended for Easy Deployment)

1. Create a Heroku account at https://heroku.com
2. Install the Heroku CLI
3. Run these commands:
   ```bash
   heroku login
   heroku create your-app-name
   git init
   git add .
   git commit -m "Initial commit"
   heroku git:remote -a your-app-name
   git push heroku main
   ```

### Option 2: DigitalOcean App Platform

1. Create a DigitalOcean account
2. Go to App Platform
3. Connect your GitHub repository
4. Configure the app:
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn --worker-class eventlet -w 1 app:app`
   - Environment Variables:
     - FLASK_SECRET_KEY
     - PORT

### Option 3: AWS Elastic Beanstalk

1. Create an AWS account
2. Install AWS CLI and EB CLI
3. Initialize EB:
   ```bash
   eb init
   eb create production
   ```

## Domain Setup

1. Purchase a domain from a registrar (e.g., GoDaddy, Namecheap)
2. Point your domain to your hosting provider
3. Set up SSL certificate (automatic with most providers)

## Environment Variables

Create a `.env` file with:
```
FLASK_SECRET_KEY=your-secure-secret-key-here
PORT=5000
```

## Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run locally:
   ```bash
   python app.py
   ```

3. Visit http://localhost:5000

## Security Notes

- Never commit `.env` file
- Use strong secret keys
- Enable HTTPS
- Set up proper CORS policies
- Implement rate limiting 