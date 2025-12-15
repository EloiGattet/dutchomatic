"""City selection logic for daily city feature."""

import json
import random
from pathlib import Path
from typing import Dict, Optional


def load_cities() -> list:
    """Charge la liste des villes depuis cities.json."""
    project_root = Path(__file__).parent.parent.parent
    cities_path = project_root / 'data' / 'cities.json'
    
    if not cities_path.exists():
        return []
    
    try:
        with open(cities_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def select_city() -> Optional[Dict]:
    """Sélectionne une ville aléatoire pour la ville du jour.
    
    Returns:
        Dictionnaire de la ville sélectionnée ou None si aucune disponible
    """
    cities = load_cities()
    
    if not cities:
        return None
    
    return random.choice(cities)

