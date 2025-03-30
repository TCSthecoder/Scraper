// Initialize Socket.IO connection
const socket = io();

// Global variables
let selectedCoin = 'bitcoin';
let priceHistory = {};

// Format number with commas and decimals
function formatNumber(num, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

// Format price with currency symbol
function formatPrice(price) {
    return `$${formatNumber(price)}`;
}

// Format percentage change
function formatChange(change) {
    const sign = change >= 0 ? '+' : '';
    const className = change >= 0 ? 'positive-change' : 'negative-change';
    return `<span class="${className}">${sign}${formatNumber(change)}%</span>`;
}

// Update price table
function updatePriceTable(data) {
    const tbody = document.getElementById('priceTable');
    tbody.innerHTML = '';

    Object.entries(data).forEach(([coin, info]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${coin.charAt(0).toUpperCase() + coin.slice(1)}</td>
            <td>${formatPrice(info.usd)}</td>
            <td>${formatChange(info.usd_24h_change)}</td>
            <td>${formatNumber(info.rsi || 0)}</td>
            <td>${formatPrice(info.ma_7 || 0)}</td>
            <td>${formatPrice(info.ma_30 || 0)}</td>
        `;
        row.addEventListener('click', () => selectCoin(coin));
        tbody.appendChild(row);
    });
}

// Update price chart
function updatePriceChart(coin, history) {
    if (!history || !history[coin]) return;

    const data = history[coin];
    const timestamps = data.map(d => new Date(d.timestamp * 1000));
    const prices = data.map(d => d.price);

    const trace = {
        x: timestamps,
        y: prices,
        type: 'scatter',
        name: coin.toUpperCase(),
        line: {
            color: '#00ff00'
        }
    };

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
            color: '#ffffff'
        },
        xaxis: {
            gridcolor: '#404040'
        },
        yaxis: {
            gridcolor: '#404040'
        }
    };

    Plotly.newPlot('priceChart', [trace], layout);
}

// Update alerts section
function updateAlerts(data) {
    const alertsList = document.getElementById('alertsList');
    alertsList.innerHTML = '';

    Object.entries(data).forEach(([coin, info]) => {
        if (info.alerts) {
            info.alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.type === 'high' ? 'high' : 'low'}`;
                alertDiv.innerHTML = `
                    <strong>${coin.toUpperCase()}</strong> price is ${alert.type === 'high' ? 'above' : 'below'} ${formatPrice(alert.threshold)}
                `;
                alertsList.appendChild(alertDiv);
            });
        }
    });
}

// Select coin for chart
function selectCoin(coin) {
    selectedCoin = coin;
    updatePriceChart(coin, priceHistory);
}

// Handle WebSocket events
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('price_update', (data) => {
    priceHistory = data.price_history;
    updatePriceTable(data.latest_data);
    updatePriceChart(selectedCoin, priceHistory);
    updateAlerts(data.latest_data);
});

// Initial data load
fetch('/api/latest')
    .then(response => response.json())
    .then(data => {
        updatePriceTable(data);
    });

fetch('/api/history')
    .then(response => response.json())
    .then(data => {
        priceHistory = data;
        updatePriceChart(selectedCoin, priceHistory);
    }); 