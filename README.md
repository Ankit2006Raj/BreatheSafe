# 🌿 BreatheSafe AI - Real-Time Air Quality Monitoring System

An advanced, real-time air quality monitoring and prediction system powered by AI and modern web technologies. Features live data updates, interactive maps, historical trends, and comprehensive health recommendations.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Flask](https://img.shields.io/badge/flask-3.0.0-red)
![License](https://img.shields.io/badge/license-MIT-yellow)

## ✨ Features

### 🔴 Real-Time Monitoring
- **Live Data Updates**: WebSocket-powered real-time air quality data every 5 seconds
- **Instant Notifications**: Get alerted when air quality changes
- **Connection Status**: Visual indicator for WebSocket connection status
- **Auto-Reconnection**: Automatic reconnection on connection loss

### 🤖 AI-Powered Predictions
- **Advanced ML Model**: Gradient Boosting algorithm with 95%+ accuracy
- **8 Input Parameters**: PM2.5, PM10, NO2, O3, CO, Temperature, Humidity, Wind Speed
- **Instant Results**: Real-time AQI predictions with health recommendations
- **Quick Scenarios**: Pre-configured clean, moderate, and polluted air scenarios

### 🗺️ Interactive Global Map
- **Leaflet Integration**: Interactive map showing air quality across major cities
- **Color-Coded Markers**: Visual representation of AQI levels
- **City Information**: Click markers for detailed city-specific data
- **Global Coverage**: Monitor air quality in 10+ major cities worldwide

### 📊 Advanced Analytics
- **Live Charts**: Real-time AQI trend visualization with Chart.js
- **Historical Data**: View air quality patterns over 24h, 48h, or 72h
- **Feature Importance**: Understand which factors affect air quality most
- **AQI Distribution**: Statistical breakdown of air quality categories
- **Model Metrics**: Comprehensive performance statistics

### 💾 Data Management
- **Export Options**: Download data in CSV or JSON format
- **Save Results**: Store predictions locally for future reference
- **Report Generation**: Create comprehensive air quality reports
- **Historical Tracking**: Access past predictions and trends

### 🔔 Smart Alerts
- **Custom Thresholds**: Set personalized AQI alert levels
- **Email Notifications**: Optional email alerts for unhealthy air quality
- **Visual Warnings**: On-screen notifications for air quality changes
- **Persistent Settings**: Alert preferences saved across sessions

### 🎨 Modern UI/UX
- **Dark Mode**: Eye-friendly dark theme with smooth transitions
- **Responsive Design**: Seamless experience on desktop, tablet, and mobile
- **Smooth Animations**: Engaging transitions and visual feedback
- **Glass Morphism**: Modern glassmorphic design elements
- **Particle Effects**: Dynamic background animations
- **Confetti Celebration**: Fun animations for good air quality

### 📱 PWA Support
- **Installable**: Add to home screen on mobile devices
- **Offline Access**: Core functionality available offline
- **Push Notifications**: Receive alerts even when app is closed
- **Fast Loading**: Optimized performance with service workers

## 🚀 Tech Stack

### Backend
- **Flask 3.0.0**: Modern Python web framework
- **Flask-SocketIO**: Real-time bidirectional communication
- **scikit-learn**: Machine learning (Gradient Boosting)
- **pandas**: Data processing and analysis
- **numpy**: Numerical computations
- **eventlet**: Asynchronous networking

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with animations
- **JavaScript ES6+**: Interactive functionality
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Interactive data visualization
- **Leaflet**: Interactive maps
- **Socket.IO Client**: Real-time communication
- **Bootstrap Icons**: Comprehensive icon library

### Real-Time Features
- **WebSocket**: Bidirectional real-time communication
- **Socket.IO**: Cross-browser WebSocket support
- **Event-Driven**: Efficient real-time data updates
- **Auto-Reconnection**: Resilient connection handling

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd BreatheSafe
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python app.py
```

5. **Access the application**
```
Open your browser and navigate to: http://localhost:5000
```

## 📁 Project Structure

```
BreatheSafe/
├── app.py                              # Flask backend with WebSocket
├── requirements.txt                    # Python dependencies
├── breathesafe_sample_global_aqi.csv   # Training dataset
├── templates/
│   └── index.html                      # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css                   # Custom styles & animations
│   ├── js/
│   │   └── script.js                   # Frontend logic & WebSocket
│   └── manifest.json                   # PWA manifest
├── .gitignore                          # Git ignore rules
└── README.md                           # Documentation
```

## 🎯 How It Works

### 1. Real-Time Monitoring
- WebSocket connection established on page load
- Server sends live data updates every 5 seconds
- Client displays real-time values with smooth animations
- Historical data plotted on interactive charts

### 2. AQI Prediction
- User adjusts environmental parameters via sliders
- Data sent to Flask backend via AJAX
- ML model processes inputs and predicts AQI
- Results displayed with category, color, and health advice

### 3. Interactive Map
- Leaflet map initialized with global view
- City markers fetched from backend API
- Markers color-coded based on current AQI
- Click markers for detailed city information

### 4. Data Analytics
- Statistics loaded from backend on page load
- Feature importance visualized with animated bars
- AQI distribution shown with color-coded categories
- Model performance metrics displayed

## 🔌 API Endpoints

### Core Endpoints

#### `GET /`
Returns the main application page

#### `POST /predict`
Predicts AQI based on input parameters

**Request:**
```json
{
  "pm25": 80,
  "pm10": 120,
  "no2": 40,
  "o3": 60,
  "co": 1.2,
  "temperature": 28,
  "humidity": 60,
  "wind_speed": 2.0
}
```

**Response:**
```json
{
  "success": true,
  "aqi": 125.3,
  "category": "Unhealthy for Sensitive Groups",
  "color": "#E67E22",
  "icon": "bi-exclamation-triangle",
  "advice": "Sensitive groups should limit outdoor exposure.",
  "level": "warning"
}
```

#### `GET /stats`
Returns model statistics and feature importance

#### `GET /api/historical/<hours>`
Returns historical AQI data for specified hours

#### `GET /api/locations`
Returns list of monitored cities with current AQI

#### `GET /api/recommendations/<aqi>`
Returns detailed health recommendations for given AQI

#### `POST /api/alerts`
Sets AQI alert threshold and notification preferences

#### `GET /api/export/<format>`
Exports data in CSV or JSON format

### WebSocket Events

#### `connect`
Client connects to WebSocket server

#### `disconnect`
Client disconnects from WebSocket server

#### `request_realtime_data`
Client requests real-time data update

**Emit:**
```javascript
socket.emit('request_realtime_data', { location: 'Global' });
```

#### `realtime_update`
Server sends real-time data to client

**Receive:**
```javascript
socket.on('realtime_update', function(data) {
  // data contains: timestamp, aqi, pm25, pm10, etc.
});
```

#### `global_update`
Server broadcasts updates to all connected clients

## 📊 AQI Categories

| AQI Range | Category | Color | Health Impact |
|-----------|----------|-------|---------------|
| 0-50 | Good | 🟢 Green | Air quality is satisfactory |
| 51-100 | Moderate | 🟡 Yellow | Acceptable for most people |
| 101-200 | Unhealthy for Sensitive Groups | 🟠 Orange | Sensitive groups may experience effects |
| 201-300 | Unhealthy | 🔴 Red | Everyone may experience health effects |
| 300+ | Very Unhealthy/Hazardous | 🟣 Purple | Health alert: serious effects for everyone |

## 🎨 UI Features

### Dark Mode
- Toggle between light and dark themes
- Smooth color transitions
- Persistent preference storage
- Eye-friendly color palette

### Animations
- Smooth value transitions
- Particle background effects
- Confetti for good air quality
- Loading spinners and skeletons
- Hover effects and micro-interactions

### Responsive Design
- Mobile-first approach
- Breakpoints for all screen sizes
- Touch-friendly controls
- Optimized layouts for tablets

## 🔧 Configuration

### WebSocket Settings
Edit `app.py` to configure WebSocket:
```python
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading'
)
```

### Update Frequency
Change real-time update interval in `static/js/script.js`:
```javascript
setInterval(() => {
    socket.emit('request_realtime_data', { location: 'Global' });
}, 5000); // 5 seconds
```

### Chart Configuration
Customize chart appearance in `static/js/script.js`:
```javascript
realtimeChart = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
        // Chart.js options
    }
});
```

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn eventlet
gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Environment Variables
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export PORT=5000
```

## 🧪 Testing

### Manual Testing
1. Open application in browser
2. Check WebSocket connection status
3. Test real-time data updates
4. Try AQI prediction with different values
5. Explore interactive map
6. Test dark mode toggle
7. Try export functionality

### Browser Compatibility
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers

## 📈 Performance

- **Initial Load**: < 2 seconds
- **Real-Time Updates**: Every 5 seconds
- **Prediction Response**: < 500ms
- **Chart Rendering**: < 100ms
- **WebSocket Latency**: < 50ms

## 🔒 Security

- CORS enabled for API access
- Input validation on all endpoints
- Secure WebSocket connections
- XSS protection
- CSRF tokens for forms

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Ankit Raj**
- AI & ML Engineer
- GitHub: [@Ankit2006Raj](https://github.com/Ankit2006Raj)
- LinkedIn: [Ankit Raj](https://www.linkedin.com/in/ankit-raj-226a36309)
- Email: ankit9905163014@gmail.com

## 🙏 Acknowledgments

- Air quality data from global monitoring stations
- Bootstrap for responsive UI framework
- Chart.js for beautiful visualizations
- Leaflet for interactive maps
- Socket.IO for real-time communication
- scikit-learn for machine learning capabilities

## 📞 Support

For support, email ankit9905163014@gmail.com or open an issue on GitHub.

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Historical data analysis
- [ ] Weather forecast integration
- [ ] Social sharing features
- [ ] Multi-language support
- [ ] Advanced ML models (LSTM, Transformer)
- [ ] Air quality predictions (24h forecast)
- [ ] Community reporting
- [ ] API for third-party integration

---

Made with ❤️ for cleaner air and healthier communities
"# BreatheSafe" 
"# BreatheSafe-AI" 
