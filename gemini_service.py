"""
Gemini AI Service for intelligent air quality analysis and recommendations
"""

import google.generativeai as genai
import os
from typing import Dict, Optional, List
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiAIService:
    """Service to provide AI-powered air quality insights using Google Gemini"""
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.model = None
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour cache for AI responses
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini AI configured successfully")
            except Exception as e:
                logger.error(f"Error configuring Gemini AI: {e}")
        else:
            logger.warning("Gemini API key not configured")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp')
        if not cached_time:
            return False
            
        return (datetime.now() - cached_time).seconds < self.cache_timeout
    
    def get_health_recommendations(self, aqi: float, pm25: float, location: str = "your area") -> Dict:
        """
        Get AI-powered personalized health recommendations based on air quality
        """
        if not self.model:
            return self._get_fallback_recommendations(aqi)
        
        cache_key = f"health_rec_{int(aqi)}_{int(pm25)}"
        
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached AI recommendations for AQI {aqi}")
            return self.cache[cache_key]['data']
        
        try:
            prompt = f"""
You are an air quality health expert. Based on the following air quality data, provide detailed, actionable health recommendations:

Location: {location}
Current AQI: {aqi}
PM2.5 Level: {pm25} µg/m³

Please provide:
1. Overall health impact assessment (2-3 sentences)
2. Specific recommendations for:
   - General population (3-4 bullet points)
   - Sensitive groups (children, elderly, respiratory patients) (3-4 bullet points)
   - Outdoor activities guidance
   - Indoor air quality tips (3-4 bullet points)
3. Protective measures to take (3-4 bullet points)
4. When to seek medical attention

Format your response as JSON with these keys:
{{
    "assessment": "overall health impact",
    "general_population": ["recommendation 1", "recommendation 2", ...],
    "sensitive_groups": ["recommendation 1", "recommendation 2", ...],
    "outdoor_activities": "guidance text",
    "indoor_tips": ["tip 1", "tip 2", ...],
    "protective_measures": ["measure 1", "measure 2", ...],
    "medical_attention": "when to seek help"
}}

Keep recommendations practical, specific, and actionable.
"""
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                text = response.text
                # Find JSON content
                start_idx = text.find('{')
                end_idx = text.rfind('}') + 1
                json_str = text[start_idx:end_idx]
                
                recommendations = json.loads(json_str)
                recommendations['source'] = 'Gemini AI'
                recommendations['timestamp'] = datetime.now().isoformat()
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': recommendations,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"Generated AI recommendations for AQI {aqi}")
                return recommendations
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response as JSON, using text format")
                return {
                    'assessment': response.text[:200],
                    'general_population': [response.text],
                    'source': 'Gemini AI (text)',
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return self._get_fallback_recommendations(aqi)
    
    def analyze_air_quality_trend(self, historical_data: List[Dict]) -> Dict:
        """
        Analyze air quality trends and provide insights
        """
        if not self.model or not historical_data:
            return {'analysis': 'Insufficient data for trend analysis', 'source': 'Fallback'}
        
        try:
            # Prepare data summary
            aqi_values = [d.get('aqi', 0) for d in historical_data[-24:]]  # Last 24 hours
            avg_aqi = sum(aqi_values) / len(aqi_values) if aqi_values else 0
            max_aqi = max(aqi_values) if aqi_values else 0
            min_aqi = min(aqi_values) if aqi_values else 0
            
            prompt = f"""
Analyze this air quality trend data and provide insights:

Time Period: Last 24 hours
Average AQI: {avg_aqi:.1f}
Maximum AQI: {max_aqi:.1f}
Minimum AQI: {min_aqi:.1f}
Data Points: {len(aqi_values)}

Provide:
1. Trend analysis (improving, worsening, or stable)
2. Key observations (2-3 points)
3. Forecast for next 6-12 hours
4. Recommended actions based on trend

Keep response concise and actionable (max 150 words).
"""
            
            response = self.model.generate_content(prompt)
            
            return {
                'analysis': response.text,
                'avg_aqi': round(avg_aqi, 1),
                'max_aqi': round(max_aqi, 1),
                'min_aqi': round(min_aqi, 1),
                'source': 'Gemini AI',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return {'analysis': 'Unable to analyze trend at this time', 'source': 'Error'}
    
    def get_personalized_advice(self, aqi: float, user_profile: Dict) -> Dict:
        """
        Get personalized advice based on user profile
        user_profile: {age_group, health_conditions, activity_level, location}
        """
        if not self.model:
            return {'advice': 'Please configure Gemini API for personalized advice', 'source': 'Fallback'}
        
        try:
            age_group = user_profile.get('age_group', 'adult')
            health_conditions = user_profile.get('health_conditions', [])
            activity_level = user_profile.get('activity_level', 'moderate')
            
            prompt = f"""
Provide personalized air quality advice for:

Current AQI: {aqi}
Age Group: {age_group}
Health Conditions: {', '.join(health_conditions) if health_conditions else 'None reported'}
Activity Level: {activity_level}

Give specific, personalized recommendations (3-5 bullet points) considering their profile.
Be empathetic and practical.
"""
            
            response = self.model.generate_content(prompt)
            
            return {
                'advice': response.text,
                'personalized': True,
                'source': 'Gemini AI',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting personalized advice: {e}")
            return {'advice': 'Unable to generate personalized advice', 'source': 'Error'}
    
    def explain_aqi_simply(self, aqi: float, pm25: float) -> str:
        """
        Explain AQI in simple, easy-to-understand language
        """
        if not self.model:
            return f"The air quality index is {aqi}. Lower numbers mean cleaner air."
        
        try:
            prompt = f"""
Explain this air quality data to a 10-year-old child in simple, friendly language:

AQI: {aqi}
PM2.5: {pm25} µg/m³

Use an analogy or comparison they can understand. Keep it to 2-3 sentences.
Be encouraging if air is good, or gently cautionary if air is poor.
"""
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating simple explanation: {e}")
            return f"The air quality is at level {aqi}. Think of it like a score - lower is better!"
    
    def compare_cities(self, city_data: List[Dict]) -> Dict:
        """
        Compare air quality across multiple cities with AI insights
        """
        if not self.model or len(city_data) < 2:
            return {'comparison': 'Need at least 2 cities to compare', 'source': 'Fallback'}
        
        try:
            cities_summary = "\n".join([
                f"- {city['name']}: AQI {city['aqi']}, PM2.5 {city.get('pm25', 'N/A')}"
                for city in city_data[:5]  # Limit to 5 cities
            ])
            
            prompt = f"""
Compare air quality across these cities and provide insights:

{cities_summary}

Provide:
1. Which city has the best air quality and why
2. Which city needs most concern
3. Interesting patterns or observations
4. General advice for residents of each city

Keep response concise (max 100 words).
"""
            
            response = self.model.generate_content(prompt)
            
            return {
                'comparison': response.text,
                'cities_analyzed': len(city_data),
                'source': 'Gemini AI',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing cities: {e}")
            return {'comparison': 'Unable to compare cities', 'source': 'Error'}
    
    def _get_fallback_recommendations(self, aqi: float) -> Dict:
        """Fallback recommendations when AI is not available"""
        if aqi <= 50:
            return {
                'assessment': 'Air quality is good. No health concerns.',
                'general_population': [
                    'Enjoy outdoor activities',
                    'No special precautions needed',
                    'Great day for exercise outside'
                ],
                'sensitive_groups': [
                    'No restrictions for sensitive groups',
                    'Safe for all outdoor activities'
                ],
                'outdoor_activities': 'Ideal conditions for all outdoor activities',
                'indoor_tips': [
                    'Open windows for fresh air',
                    'No air purifier needed'
                ],
                'protective_measures': ['No special measures needed'],
                'medical_attention': 'Not applicable for good air quality',
                'source': 'Fallback',
                'timestamp': datetime.now().isoformat()
            }
        elif aqi <= 100:
            return {
                'assessment': 'Air quality is acceptable. Unusually sensitive people may experience minor issues.',
                'general_population': [
                    'Generally safe for outdoor activities',
                    'Monitor air quality if exercising outdoors',
                    'Stay hydrated'
                ],
                'sensitive_groups': [
                    'Consider reducing prolonged outdoor exertion',
                    'Monitor symptoms',
                    'Keep rescue medications handy'
                ],
                'outdoor_activities': 'Generally safe, but sensitive individuals should monitor symptoms',
                'indoor_tips': [
                    'Keep windows closed during peak pollution hours',
                    'Consider using air purifier',
                    'Maintain good ventilation'
                ],
                'protective_measures': [
                    'Sensitive individuals may wear masks outdoors',
                    'Limit time in high-traffic areas'
                ],
                'medical_attention': 'Seek help if experiencing unusual respiratory symptoms',
                'source': 'Fallback',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'assessment': 'Air quality is unhealthy. Everyone may experience health effects.',
                'general_population': [
                    'Limit outdoor activities',
                    'Wear N95 masks if going outside',
                    'Stay indoors as much as possible',
                    'Avoid strenuous activities'
                ],
                'sensitive_groups': [
                    'Avoid all outdoor activities',
                    'Stay indoors with air filtration',
                    'Keep medications readily available',
                    'Monitor symptoms closely'
                ],
                'outdoor_activities': 'Avoid all outdoor activities',
                'indoor_tips': [
                    'Keep all windows and doors closed',
                    'Use HEPA air purifiers',
                    'Create a clean air room',
                    'Avoid activities that increase indoor pollution'
                ],
                'protective_measures': [
                    'Wear N95/N99 masks if must go outside',
                    'Limit physical exertion',
                    'Stay in air-conditioned spaces',
                    'Check air quality frequently'
                ],
                'medical_attention': 'Seek immediate medical attention if experiencing difficulty breathing, chest pain, or severe symptoms',
                'source': 'Fallback',
                'timestamp': datetime.now().isoformat()
            }


# Global instance
gemini_service = GeminiAIService()
