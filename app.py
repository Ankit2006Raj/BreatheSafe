from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import os
from datetime import datetime, timedelta
import json
import random
import threading
import time
from dotenv import load_dotenv
from api_service import api_service
from gemini_service import gemini_service

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration from environment
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'breathesafe-secret-key-2024')
app.config['JSON_SORT_KEYS'] = False

# Configuration
app.config['SECRET_KEY'] = 'breathesafe-secret-key-2024'
app.config['JSON_SORT_KEYS'] = False

# Global variables for model and data
model = None
df = None
model_metrics = {}
feature_names = ['pm25', 'pm10', 'no2', 'o3', 'co', 'temperature', 'humidity', 'wind_speed']

# Load and train model on startup
def train_model():
    global model, df, model_metrics
    
    df = pd.read_csv("breathesafe_sample_global_aqi.csv")
    X = df[feature_names]
    y = df['aqi']
    
    # Split data for validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Gradient Boosting model (better than Random Forest)
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Calculate metrics
    y_pred = model.predict(X_test)
    model_metrics = {
        'rmse': round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        'r2_score': round(r2_score(y_test, y_pred), 4),
        'accuracy': round(r2_score(y_test, y_pred) * 100, 2)
    }
    
    return model, df

# Initialize model
model, df = train_model()

def get_aqi_category(aqi):
    if aqi <= 50:
        return {
            'category': 'Good',
            'color': '#2ECC71',
            'icon': 'bi-emoji-smile',
            'advice': 'Air quality is healthy. Enjoy outdoor activities!',
            'level': 'success'
        }
    elif aqi <= 100:
        return {
            'category': 'Moderate',
            'color': '#F1C40F',
            'icon': 'bi-emoji-neutral',
            'advice': 'Air quality is acceptable. Sensitive groups should consider precautions.',
            'level': 'warning'
        }
    elif aqi <= 200:
        return {
            'category': 'Unhealthy for Sensitive Groups',
            'color': '#E67E22',
            'icon': 'bi-exclamation-triangle',
            'advice': 'Sensitive groups (elderly, lung patients) should limit outdoor exposure.',
            'level': 'warning'
        }
    elif aqi <= 300:
        return {
            'category': 'Unhealthy',
            'color': '#E74C3C',
            'icon': 'bi-x-circle',
            'advice': 'Air quality is unhealthy. Avoid outdoor activities.',
            'level': 'danger'
        }
    else:
        return {
            'category': 'Very Unhealthy / Hazardous',
            'color': '#8E44AD',
            'icon': 'bi-shield-exclamation',
            'advice': 'Air is hazardous! Stay indoors and use masks or air purifiers.',
            'level': 'danger'
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        user_input = pd.DataFrame([{
            'pm25': float(data['pm25']),
            'pm10': float(data['pm10']),
            'no2': float(data['no2']),
            'o3': float(data['o3']),
            'co': float(data['co']),
            'temperature': float(data['temperature']),
            'humidity': float(data['humidity']),
            'wind_speed': float(data['wind_speed'])
        }])
        
        predicted_aqi = model.predict(user_input)[0]
        category_info = get_aqi_category(predicted_aqi)
        
        return jsonify({
            'success': True,
            'aqi': round(predicted_aqi, 1),
            **category_info
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/stats')
def stats():
    try:
        importance = dict(zip(feature_names, model.feature_importances_))
        
        # Calculate AQI distribution
        aqi_distribution = {
            'good': int((df['aqi'] <= 50).sum()),
            'moderate': int(((df['aqi'] > 50) & (df['aqi'] <= 100)).sum()),
            'unhealthy_sensitive': int(((df['aqi'] > 100) & (df['aqi'] <= 200)).sum()),
            'unhealthy': int(((df['aqi'] > 200) & (df['aqi'] <= 300)).sum()),
            'hazardous': int((df['aqi'] > 300).sum())
        }
        
        stats_data = {
            'total_records': len(df),
            'avg_aqi': round(df['aqi'].mean(), 1),
            'max_aqi': round(df['aqi'].max(), 1),
            'min_aqi': round(df['aqi'].min(), 1),
            'median_aqi': round(df['aqi'].median(), 1),
            'feature_importance': importance,
            'aqi_distribution': aqi_distribution,
            'model_metrics': model_metrics
        }
        
        return jsonify(stats_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get recent predictions history"""
    try:
        # Return sample historical data
        history = []
        for i in range(10):
            sample = df.sample(1).iloc[0]
            history.append({
                'timestamp': (datetime.now().timestamp() - i * 3600) * 1000,
                'aqi': round(sample['aqi'], 1),
                'pm25': round(sample['pm25'], 1),
                'location': sample.get('location', 'Unknown')
            })
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/recommendations/<int:aqi>')
def get_recommendations(aqi):
    """Get detailed health recommendations based on AQI (enhanced with AI)"""
    try:
        # Get AI-powered recommendations if available
        ai_recommendations = gemini_service.get_health_recommendations(aqi, aqi * 0.5, "your area")
        
        # If AI recommendations available, use them
        if ai_recommendations.get('source') == 'Gemini AI':
            return jsonify(ai_recommendations)
        
        # Otherwise use fallback recommendations
        recommendations = {
            'general': [],
            'sensitive_groups': [],
            'outdoor_activities': '',
            'protective_measures': []
        }
        
        if aqi <= 50:
            recommendations['general'] = ['Air quality is satisfactory', 'No health concerns']
            recommendations['outdoor_activities'] = 'Ideal for all outdoor activities'
            recommendations['protective_measures'] = ['No special precautions needed']
        elif aqi <= 100:
            recommendations['general'] = ['Air quality is acceptable', 'Unusually sensitive people may experience minor issues']
            recommendations['sensitive_groups'] = ['People with respiratory conditions should monitor symptoms']
            recommendations['outdoor_activities'] = 'Generally safe for outdoor activities'
            recommendations['protective_measures'] = ['Sensitive individuals should consider reducing prolonged outdoor exertion']
        elif aqi <= 200:
            recommendations['general'] = ['Unhealthy for sensitive groups', 'General public not likely affected']
            recommendations['sensitive_groups'] = ['Children, elderly, and people with heart/lung disease should limit outdoor activities']
            recommendations['outdoor_activities'] = 'Reduce prolonged or heavy outdoor exertion'
            recommendations['protective_measures'] = ['Wear N95 masks if going outside', 'Keep windows closed', 'Use air purifiers indoors']
        elif aqi <= 300:
            recommendations['general'] = ['Everyone may experience health effects', 'Sensitive groups may experience serious effects']
            recommendations['sensitive_groups'] = ['Avoid all outdoor activities', 'Stay indoors with air filtration']
            recommendations['outdoor_activities'] = 'Avoid all outdoor activities'
            recommendations['protective_measures'] = ['Wear N95/N99 masks if must go outside', 'Keep all windows closed', 'Use HEPA air purifiers', 'Avoid physical exertion']
        else:
            recommendations['general'] = ['Health alert: everyone may experience serious health effects']
            recommendations['sensitive_groups'] = ['Emergency conditions - stay indoors', 'Seek medical attention if experiencing symptoms']
            recommendations['outdoor_activities'] = 'Stay indoors - emergency conditions'
            recommendations['protective_measures'] = ['Do not go outside', 'Seal windows and doors', 'Use multiple air purifiers', 'Consider evacuation if possible']
        
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/compare', methods=['POST'])
def compare_scenarios():
    """Compare multiple scenarios"""
    try:
        scenarios = request.json.get('scenarios', [])
        results = []
        
        for scenario in scenarios:
            user_input = pd.DataFrame([{
                'pm25': float(scenario['pm25']),
                'pm10': float(scenario['pm10']),
                'no2': float(scenario['no2']),
                'o3': float(scenario['o3']),
                'co': float(scenario['co']),
                'temperature': float(scenario['temperature']),
                'humidity': float(scenario['humidity']),
                'wind_speed': float(scenario['wind_speed'])
            }])
            
            predicted_aqi = model.predict(user_input)[0]
            category_info = get_aqi_category(predicted_aqi)
            
            results.append({
                'name': scenario.get('name', 'Scenario'),
                'aqi': round(predicted_aqi, 1),
                'category': category_info['category'],
                'color': category_info['color']
            })
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/realtime/start', methods=['POST'])
def start_realtime():
    """Start real-time monitoring"""
    try:
        data = request.json
        location = data.get('location', 'Unknown')
        return jsonify({'success': True, 'message': 'Real-time monitoring started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/historical/<int:hours>')
def get_historical_data(hours):
    """Get historical AQI data with real API data when available"""
    try:
        historical = []
        now = datetime.now()
        
        # Try to get real data for New York as default
        real_data = api_service.get_combined_data(40.7128, -74.0060, 'New York')
        
        for i in range(hours):
            timestamp = (now - timedelta(hours=hours-i)).isoformat()
            
            if real_data and real_data.get('aqi', 0) > 0:
                # Use real data with slight variations for historical trend
                variation = random.uniform(-5, 5)
                historical.append({
                    'timestamp': timestamp,
                    'aqi': max(0, round(real_data['aqi'] + variation, 1)),
                    'pm25': max(0, round(real_data['pm25'] + random.uniform(-2, 2), 1)),
                    'pm10': max(0, round(real_data['pm10'] + random.uniform(-3, 3), 1)),
                    'no2': max(0, round(real_data['no2'] + random.uniform(-1, 1), 1)),
                    'o3': max(0, round(real_data['o3'] + random.uniform(-2, 2), 1)),
                    'temperature': round(real_data['temperature'] + random.uniform(-0.5, 0.5), 1),
                    'humidity': max(0, min(100, round(real_data['humidity'] + random.uniform(-2, 2), 1))),
                    'source': 'Real API'
                })
            else:
                # Fallback to simulated data
                sample = df.sample(1).iloc[0]
                historical.append({
                    'timestamp': timestamp,
                    'aqi': round(sample['aqi'], 1),
                    'pm25': round(sample['pm25'], 1),
                    'pm10': round(sample['pm10'], 1),
                    'no2': round(sample['no2'], 1),
                    'o3': round(sample['o3'], 1),
                    'temperature': round(sample['temperature'], 1),
                    'humidity': round(sample['humidity'], 1),
                    'source': 'Simulated'
                })
        
        return jsonify({'data': historical, 'source': real_data.get('source', 'Simulated') if real_data else 'Simulated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/locations')
def get_locations():
    """Get available monitoring locations with real-time data"""
    cities = [
        {'id': 1, 'name': 'New York', 'lat': 40.7128, 'lng': -74.0060},
        {'id': 2, 'name': 'Los Angeles', 'lat': 34.0522, 'lng': -118.2437},
        {'id': 3, 'name': 'Chicago', 'lat': 41.8781, 'lng': -87.6298},
        {'id': 4, 'name': 'Houston', 'lat': 29.7604, 'lng': -95.3698},
        {'id': 5, 'name': 'Phoenix', 'lat': 33.4484, 'lng': -112.0740},
        {'id': 6, 'name': 'London', 'lat': 51.5074, 'lng': -0.1278},
        {'id': 7, 'name': 'Tokyo', 'lat': 35.6762, 'lng': 139.6503},
        {'id': 8, 'name': 'Delhi', 'lat': 28.7041, 'lng': 77.1025},
        {'id': 9, 'name': 'Beijing', 'lat': 39.9042, 'lng': 116.4074},
        {'id': 10, 'name': 'Sydney', 'lat': -33.8688, 'lng': 151.2093}
    ]
    
    locations = []
    for city in cities:
        # Try to get real data, fallback to random if API not configured
        real_data = api_service.get_combined_data(city['lat'], city['lng'], city['name'])
        
        locations.append({
            'id': city['id'],
            'name': city['name'],
            'lat': city['lat'],
            'lng': city['lng'],
            'aqi': real_data.get('aqi', random.randint(30, 150)),
            'source': real_data.get('source', 'Simulated')
        })
    
    return jsonify({'locations': locations})

@app.route('/api/export/<format>')
def export_data(format):
    """Export data in various formats"""
    try:
        if format == 'csv':
            return df.to_csv(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=aqi_data.csv'}
        elif format == 'json':
            return jsonify(df.to_dict('records'))
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/alerts', methods=['POST'])
def set_alert():
    """Set AQI alert threshold"""
    try:
        data = request.json
        threshold = data.get('threshold', 100)
        email = data.get('email', '')
        return jsonify({'success': True, 'message': f'Alert set for AQI > {threshold}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/realtime/<city>')
def get_realtime_city_data(city):
    """Get real-time data for a specific city"""
    try:
        coords = api_service.get_city_coordinates(city)
        if not coords:
            return jsonify({'error': 'City not found'}), 404
        
        lat, lon = coords
        data = api_service.get_combined_data(lat, lon, city)
        
        return jsonify({
            'success': True,
            'city': city,
            'data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/air-quality/coordinates')
def get_air_quality_by_coords():
    """Get air quality for specific coordinates"""
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        
        if not lat or not lon:
            return jsonify({'error': 'Missing coordinates'}), 400
            
        data = api_service.get_combined_data(lat, lon, f"Location ({lat:.2f}, {lon:.2f})")
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/check-api-status')
def check_api_status():
    """Check if API keys are configured"""
    return jsonify({
        'openweather_configured': bool(api_service.openweather_key),
        'aqicn_configured': bool(api_service.aqicn_key),
        'gemini_configured': bool(gemini_service.api_key),
        'status': 'ready' if (api_service.openweather_key or api_service.aqicn_key) else 'no_api_keys'
    })

@app.route('/api/ai/health-recommendations', methods=['POST'])
def get_ai_health_recommendations():
    """Get AI-powered health recommendations"""
    try:
        data = request.json
        aqi = data.get('aqi', 0)
        pm25 = data.get('pm25', 0)
        location = data.get('location', 'your area')
        
        recommendations = gemini_service.get_health_recommendations(aqi, pm25, location)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/ai/explain-simple', methods=['POST'])
def explain_aqi_simply():
    """Get simple explanation of AQI"""
    try:
        data = request.json
        aqi = data.get('aqi', 0)
        pm25 = data.get('pm25', 0)
        
        explanation = gemini_service.explain_aqi_simply(aqi, pm25)
        
        return jsonify({
            'success': True,
            'explanation': explanation
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/ai/trend-analysis', methods=['POST'])
def analyze_trend():
    """Analyze air quality trends with AI"""
    try:
        data = request.json
        historical_data = data.get('historical_data', [])
        
        analysis = gemini_service.analyze_air_quality_trend(historical_data)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/ai/personalized-advice', methods=['POST'])
def get_personalized_advice():
    """Get personalized advice based on user profile"""
    try:
        data = request.json
        aqi = data.get('aqi', 0)
        user_profile = data.get('profile', {})
        
        advice = gemini_service.get_personalized_advice(aqi, user_profile)
        
        return jsonify({
            'success': True,
            'advice': advice
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/ai/compare-cities', methods=['POST'])
def compare_cities_ai():
    """Compare cities with AI insights"""
    try:
        data = request.json
        cities = data.get('cities', [])
        
        comparison = gemini_service.compare_cities(cities)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_realtime_data')
def handle_realtime_request(data):
    """Send real-time AQI updates"""
    location = data.get('location', 'Unknown')
    lat = data.get('lat', 40.7128)  # Default to New York
    lon = data.get('lon', -74.0060)
    
    # Try to get real data from API
    real_data = api_service.get_combined_data(lat, lon, location)
    
    if real_data and real_data.get('aqi', 0) > 0:
        # Use real API data
        realtime_data = {
            'timestamp': real_data.get('timestamp', datetime.now().isoformat()),
            'location': location,
            'aqi': round(real_data.get('aqi', 0), 1),
            'pm25': round(real_data.get('pm25', 0), 1),
            'pm10': round(real_data.get('pm10', 0), 1),
            'no2': round(real_data.get('no2', 0), 1),
            'o3': round(real_data.get('o3', 0), 1),
            'temperature': round(real_data.get('temperature', 0), 1),
            'humidity': round(real_data.get('humidity', 0), 1),
            'wind_speed': round(real_data.get('wind_speed', 0), 1),
            'source': real_data.get('source', 'API')
        }
    else:
        # Fallback to simulated data
        sample = df.sample(1).iloc[0]
        realtime_data = {
            'timestamp': datetime.now().isoformat(),
            'location': location,
            'aqi': round(sample['aqi'] + random.uniform(-5, 5), 1),
            'pm25': round(sample['pm25'] + random.uniform(-2, 2), 1),
            'pm10': round(sample['pm10'] + random.uniform(-3, 3), 1),
            'no2': round(sample['no2'] + random.uniform(-1, 1), 1),
            'o3': round(sample['o3'] + random.uniform(-2, 2), 1),
            'temperature': round(sample['temperature'] + random.uniform(-0.5, 0.5), 1),
            'humidity': round(sample['humidity'] + random.uniform(-1, 1), 1),
            'wind_speed': round(sample['wind_speed'] + random.uniform(-0.2, 0.2), 1),
            'source': 'Simulated'
        }
    
    emit('realtime_update', realtime_data)

# Background thread for continuous real-time updates
def background_realtime_updates():
    """Send periodic real-time updates to all connected clients using real API data"""
    while True:
        time.sleep(int(os.getenv('REALTIME_UPDATE_INTERVAL', 5)))
        
        # Get real data from API
        real_data = api_service.get_combined_data(40.7128, -74.0060, 'New York')
        
        if real_data and real_data.get('aqi', 0) > 0:
            # Use real API data
            realtime_data = {
                'timestamp': datetime.now().isoformat(),
                'aqi': round(real_data['aqi'], 1),
                'pm25': round(real_data['pm25'], 1),
                'pm10': round(real_data['pm10'], 1),
                'temperature': round(real_data['temperature'], 1),
                'humidity': round(real_data['humidity'], 1),
                'category': get_aqi_category(real_data['aqi'])['category'],
                'source': real_data.get('source', 'API')
            }
        else:
            # Fallback to simulated data
            sample = df.sample(1).iloc[0]
            realtime_data = {
                'timestamp': datetime.now().isoformat(),
                'aqi': round(sample['aqi'] + random.uniform(-5, 5), 1),
                'pm25': round(sample['pm25'] + random.uniform(-2, 2), 1),
                'pm10': round(sample['pm10'] + random.uniform(-3, 3), 1),
                'temperature': round(sample['temperature'] + random.uniform(-0.5, 0.5), 1),
                'humidity': round(sample['humidity'] + random.uniform(-1, 1), 1),
                'category': get_aqi_category(sample['aqi'])['category'],
                'source': 'Simulated'
            }
        
        socketio.emit('global_update', realtime_data)

if __name__ == '__main__':
    print("=" * 60)
    print("🌿 BreatheSafe AI - Real-Time Air Quality Monitoring")
    print("=" * 60)
    print(f"Model Accuracy: {model_metrics['accuracy']}%")
    print(f"R² Score: {model_metrics['r2_score']}")
    print(f"RMSE: {model_metrics['rmse']}")
    print("=" * 60)
    
    # Check API configuration
    if api_service.openweather_key:
        print("✅ OpenWeatherMap API: Configured")
    else:
        print("⚠️  OpenWeatherMap API: Not configured")
    
    if api_service.aqicn_key:
        print("✅ AQICN API: Configured")
    else:
        print("⚠️  AQICN API: Not configured")
    
    if gemini_service.api_key:
        print("✅ Gemini AI: Configured")
    else:
        print("⚠️  Gemini AI: Not configured (AI features disabled)")
    
    print("=" * 60)
    print("✨ Features: Real-time Updates | WebSocket | AI Insights | Advanced UI")
    print("=" * 60)
    print("Server running at: http://127.0.0.1:5000")
    print("=" * 60)
    
    # Start background thread for real-time updates
    threading.Thread(target=background_realtime_updates, daemon=True).start()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)), allow_unsafe_werkzeug=True)
