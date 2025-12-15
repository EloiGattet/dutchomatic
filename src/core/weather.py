"""Weather API integration for city weather information."""

import json
from typing import Optional, Dict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import socket
import re


def get_weather(city: Dict) -> Optional[Dict]:
    """Récupère la météo actuelle pour une ville.
    
    Utilise wttr.in (gratuit, sans clé API).
    Si pas de connexion internet, retourne None.
    
    Args:
        city: Dictionnaire de la ville avec 'gps' (lat, lon) et 'name'
    
    Returns:
        Dictionnaire avec 'temp', 'description', 'emoji' ou None
    """
    gps = city.get('gps', {})
    if not gps.get('lat') or not gps.get('lon'):
        return None
    
    # Vérifier la connexion internet
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
    except OSError:
        # Pas de connexion internet
        return None
    
    try:
        # API wttr.in (gratuite, sans clé)
        # Format: wttr.in/?format=j1 pour JSON
        city_name = city.get('name', '').replace(' ', '+')
        url = f"https://wttr.in/{city_name}?format=j1&lang=fr"
        
        request = Request(url)
        request.add_header('User-Agent', 'curl/7.68.0')  # wttr.in préfère curl
        
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            # Extraire les données de la réponse wttr.in
            current = data.get('current_condition', [{}])[0]
            if not current:
                return None
            
            temp = current.get('temp_C', '0')
            try:
                temp = int(temp)
            except (ValueError, TypeError):
                temp = 0
            
            # Description en français
            desc = current.get('lang_fr', [{}])[0].get('value', '')
            if not desc:
                desc = current.get('weatherDesc', [{}])[0].get('value', '')
            
            # Code météo pour déterminer l'emoji
            weather_code = current.get('weatherCode', '113')
            
            # Mapper les codes météo wttr.in vers des emojis
            # Codes principaux: 113=clear, 116=partly cloudy, 119=cloudy, etc.
            emoji_map = {
                '113': '☀️',   # Clear/Sunny
                '116': '⛅',   # Partly cloudy
                '119': '☁️',   # Cloudy
                '122': '☁️',   # Overcast
                '143': '🌫️',  # Mist
                '176': '🌦️',  # Patchy rain
                '179': '🌨️',  # Patchy snow
                '182': '🌨️',  # Patchy sleet
                '185': '🌨️',  # Patchy freezing drizzle
                '200': '⛈️',   # Thundery outbreaks
                '227': '🌨️',  # Blowing snow
                '230': '🌨️',  # Blizzard
                '248': '🌫️',  # Fog
                '260': '🌫️',  # Freezing fog
                '263': '🌦️',  # Patchy light drizzle
                '266': '🌧️',  # Light drizzle
                '281': '🌧️',  # Freezing drizzle
                '284': '🌧️',  # Heavy freezing drizzle
                '293': '🌦️',  # Patchy light rain
                '296': '🌧️',  # Light rain
                '299': '🌧️',  # Moderate rain
                '302': '🌧️',  # Heavy rain
                '305': '🌧️',  # Heavy rain
                '308': '🌧️',  # Heavy rain
                '311': '🌧️',  # Light freezing rain
                '314': '🌧️',  # Moderate/heavy freezing rain
                '317': '🌧️',  # Light sleet
                '320': '🌧️',  # Moderate/heavy sleet
                '323': '❄️',   # Patchy light snow
                '326': '❄️',   # Light snow
                '329': '❄️',   # Patchy moderate snow
                '332': '❄️',   # Moderate snow
                '335': '❄️',   # Patchy heavy snow
                '338': '❄️',   # Heavy snow
                '350': '🌨️',  # Ice pellets
                '353': '🌦️',  # Light rain shower
                '356': '🌧️',  # Moderate/heavy rain shower
                '359': '🌧️',  # Torrential rain shower
                '362': '🌨️',  # Light sleet showers
                '365': '🌨️',  # Moderate/heavy sleet showers
                '368': '❄️',   # Light snow showers
                '371': '❄️',   # Moderate/heavy snow showers
                '374': '🌨️',  # Light showers of ice pellets
                '377': '🌨️',  # Moderate/heavy showers of ice pellets
                '386': '⛈️',   # Patchy light rain with thunder
                '389': '⛈️',   # Moderate/heavy rain with thunder
                '392': '⛈️',   # Patchy light snow with thunder
                '395': '⛈️',   # Moderate/heavy snow with thunder
            }
            
            # Utiliser le code météo ou chercher dans la description
            emoji = emoji_map.get(weather_code, '🌤️')
            
            # Si pas trouvé par code, essayer de deviner depuis la description
            if emoji == '🌤️' and desc:
                desc_lower = desc.lower()
                if 'soleil' in desc_lower or 'clair' in desc_lower or 'ensoleillé' in desc_lower:
                    emoji = '☀️'
                elif 'nuage' in desc_lower or 'couvert' in desc_lower:
                    emoji = '☁️'
                elif 'pluie' in desc_lower or 'averse' in desc_lower:
                    emoji = '🌧️'
                elif 'neige' in desc_lower:
                    emoji = '❄️'
                elif 'orage' in desc_lower or 'tonnerre' in desc_lower:
                    emoji = '⛈️'
                elif 'brouillard' in desc_lower or 'brume' in desc_lower:
                    emoji = '🌫️'
            
            return {
                'temp': temp,
                'description': desc.capitalize() if desc else '',
                'emoji': emoji
            }
    
    except (URLError, HTTPError, socket.timeout, json.JSONDecodeError, KeyError, IndexError) as e:
        # Erreur réseau ou API, on ignore silencieusement
        return None


def format_weather_line(weather: Dict) -> str:
    """Formate une ligne de météo pour l'impression.
    
    Args:
        weather: Dictionnaire de météo avec 'temp', 'emoji', 'description'
    
    Returns:
        Ligne formatée avec emoji, température et description
    """
    temp = weather.get('temp', 0)
    emoji = weather.get('emoji', '🌤️')
    description = weather.get('description', '')
    
    if description:
        return f"{emoji} {temp}°C — {description}"
    else:
        return f"{emoji} {temp}°C"

