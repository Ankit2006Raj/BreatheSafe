"""
API Service for fetching real-time air quality and weather data
Supports OpenWeatherMap and AQICN APIs
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherAPIService:
    """Service to fetch real-time weather and air quality data"""
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.openweather_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.aqicn_key = os.getenv('AQICN_API_KEY', '')
        self.cache = {}
        self.cache_timeout = int(os.getenv('CACHE_TIMEOUT', 300))  # 5 minutes
        
        # Log configuration status
        if self.openweather_key:
            logger.info(f"OpenWeatherMap API configured: {self.openweather_key[:10]}...")
        if self.aqicn_key:
            logger.info(f"AQICN API configured: {self.aqicn_key[:10]}...")
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp')
        if not cached_time:
            return False
            
        return (datetime.now() - cached_time).seconds < self.cache_timeout
    
    def get_air_quality_openweather(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Fetch air quality data from OpenWeatherMap API
        API Docs: https://openweathermap.org/api/air-pollution
        """
        if not self.openweather_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None
        
        cache_key = f"ow_aqi_{lat}_{lon}"
        
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached data for {cache_key}")
            return self.cache[cache_key]['data']
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'list' in data and len(data['list']) > 0:
                components = data['list'][0]['components']
                aqi = data['list'][0]['main']['aqi']
                
                result = {
                    'aqi': self._convert_openweather_aqi(aqi),
                    'pm25': components.get('pm2_5', 0),
                    'pm10': components.get('pm10', 0),
                    'no2': components.get('no2', 0),
                    'o3': components.get('o3', 0),
                    'co': components.get('co', 0) / 1000,  # Convert to ppm
                    'timestamp': datetime.now().isoformat(),
                    'source': 'OpenWeatherMap'
                }
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"Fetched air quality data for lat={lat}, lon={lon}")
                return result
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OpenWeatherMap data: {e}")
            return None
    
    def get_weather_data(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Fetch weather data from OpenWeatherMap API
        API Docs: https://openweathermap.org/current
        """
        if not self.openweather_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None
        
        cache_key = f"ow_weather_{lat}_{lon}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'timestamp': datetime.now().isoformat(),
                'source': 'OpenWeatherMap'
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Fetched weather data for lat={lat}, lon={lon}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
    
    def get_air_quality_aqicn(self, city: str) -> Optional[Dict]:
        """
        Fetch air quality data from AQICN (World Air Quality Index)
        API Docs: https://aqicn.org/json-api/doc/
        """
        if not self.aqicn_key:
            logger.warning("AQICN API key not configured")
            return None
        
        cache_key = f"aqicn_{city}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            url = f"https://api.waqi.info/feed/{city}/"
            params = {'token': self.aqicn_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                aqi_data = data['data']
                iaqi = aqi_data.get('iaqi', {})
                
                result = {
                    'aqi': aqi_data.get('aqi', 0),
                    'pm25': iaqi.get('pm25', {}).get('v', 0),
                    'pm10': iaqi.get('pm10', {}).get('v', 0),
                    'no2': iaqi.get('no2', {}).get('v', 0),
                    'o3': iaqi.get('o3', {}).get('v', 0),
                    'co': iaqi.get('co', {}).get('v', 0),
                    'temperature': iaqi.get('t', {}).get('v', 0),
                    'humidity': iaqi.get('h', {}).get('v', 0),
                    'wind_speed': iaqi.get('w', {}).get('v', 0),
                    'city': aqi_data.get('city', {}).get('name', city),
                    'timestamp': aqi_data.get('time', {}).get('iso', datetime.now().isoformat()),
                    'source': 'AQICN'
                }
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"Fetched AQICN data for {city}")
                return result
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching AQICN data: {e}")
            return None
    
    def get_combined_data(self, lat: float, lon: float, city: str = None) -> Dict:
        """
        Get combined air quality and weather data
        Tries multiple sources and combines the best available data
        """
        result = {
            'aqi': 0,
            'pm25': 0,
            'pm10': 0,
            'no2': 0,
            'o3': 0,
            'co': 0,
            'temperature': 0,
            'humidity': 0,
            'wind_speed': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'Simulated',
            'location': city or f"{lat},{lon}"
        }
        
        has_real_data = False
        
        # Try OpenWeatherMap first
        if self.openweather_key:
            try:
                aqi_data = self.get_air_quality_openweather(lat, lon)
                weather_data = self.get_weather_data(lat, lon)
                
                if aqi_data:
                    result.update(aqi_data)
                    has_real_data = True
                    logger.info(f"Using OpenWeatherMap AQI data: {aqi_data['aqi']}")
                
                if weather_data:
                    result.update({
                        'temperature': weather_data['temperature'],
                        'humidity': weather_data['humidity'],
                        'wind_speed': weather_data['wind_speed']
                    })
                    has_real_data = True
                    logger.info(f"Using OpenWeatherMap weather data: {weather_data['temperature']}°C")
            except Exception as e:
                logger.error(f"Error getting OpenWeatherMap data: {e}")
        
        # Try AQICN as fallback or supplement
        if city and self.aqicn_key and not has_real_data:
            try:
                aqicn_data = self.get_air_quality_aqicn(city)
                if aqicn_data and aqicn_data.get('aqi', 0) > 0:
                    result.update(aqicn_data)
                    has_real_data = True
                    logger.info(f"Using AQICN data: {aqicn_data['aqi']}")
            except Exception as e:
                logger.error(f"Error getting AQICN data: {e}")
        
        # If no real data, log warning
        if not has_real_data:
            logger.warning(f"No real API data available for {city or f'{lat},{lon}'}, returning empty result")
        
        return result
    
    def _convert_openweather_aqi(self, ow_aqi: int) -> float:
        """
        Convert OpenWeatherMap AQI (1-5 scale) to US AQI (0-500 scale)
        OpenWeather scale: 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
        """
        conversion = {
            1: 25,   # Good
            2: 75,   # Fair
            3: 125,  # Moderate
            4: 200,  # Poor
            5: 350   # Very Poor
        }
        return conversion.get(ow_aqi, 0)
    
    def get_city_coordinates(self, city: str) -> Optional[tuple]:
        """Get coordinates for a city name"""
        city_coords = {
            'New York': (40.7128, -74.0060),
            'Los Angeles': (34.0522, -118.2437),
            'Chicago': (41.8781, -87.6298),
            'Houston': (29.7604, -95.3698),
            'Phoenix': (33.4484, -112.0740),
            'London': (51.5074, -0.1278),
            'Tokyo': (35.6762, 139.6503),
            'Delhi': (28.7041, 77.1025),
            'Beijing': (39.9042, 116.4074),
            'Sydney': (-33.8688, 151.2093),
            'Paris': (48.8566, 2.3522),
            'Berlin': (52.5200, 13.4050),
            'Mumbai': (19.0760, 72.8777),
            'Shanghai': (31.2304, 121.4737),
            'Moscow': (55.7558, 37.6173)
        }
        return city_coords.get(city)


# Global instance
api_service = WeatherAPIService()
