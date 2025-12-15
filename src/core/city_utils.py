"""Utilities for city mapping and image generation."""

from pathlib import Path
from typing import Tuple, Optional, Dict

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None


# Bornes GPS des Pays-Bas (valeurs optimales calibrées)
# Les valeurs ajustées sont chargées depuis config/map_mapping.json
DEFAULT_BOUNDS = {
    "north": 53.750000,  # Latitude maximale (nord)
    "south": 50.520000,  # Latitude minimale (sud)
    "east": 7.227500,    # Longitude maximale (est)
    "west": 3.150000     # Longitude minimale (ouest)
}

DEFAULT_OFFSETS = {
    "x": 0,  # Décalage horizontal
    "y": 0   # Décalage vertical
}


def load_mapping_config() -> tuple:
    """Charge la configuration de mapping depuis config/map_mapping.json.
    
    Returns:
        Tuple (bounds, offsets)
    """
    import json
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / 'config' / 'map_mapping.json'
    
    bounds = DEFAULT_BOUNDS.copy()
    offsets = DEFAULT_OFFSETS.copy()
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                bounds.update(config.get('bounds', {}))
                offsets.update(config.get('offsets', {}))
        except Exception:
            pass  # Utiliser les valeurs par défaut en cas d'erreur
    
    return bounds, offsets


def gps_to_image_coords(
    lat: float,
    lon: float,
    image_width: int,
    image_height: int,
    bounds: dict = None,
    offsets: dict = None
) -> Tuple[int, int]:
    """Convertit des coordonnées GPS en coordonnées d'image.
    
    Args:
        lat: Latitude GPS
        lon: Longitude GPS
        image_width: Largeur de l'image en pixels
        image_height: Hauteur de l'image en pixels
        bounds: Dictionnaire avec 'north', 'south', 'east', 'west' (défaut: chargé depuis config)
        offsets: Dictionnaire avec 'x', 'y' pour décaler (défaut: chargé depuis config)
    
    Returns:
        Tuple (x, y) en coordonnées d'image
    """
    if bounds is None or offsets is None:
        loaded_bounds, loaded_offsets = load_mapping_config()
        if bounds is None:
            bounds = loaded_bounds
        if offsets is None:
            offsets = loaded_offsets
    
    # Normaliser les coordonnées GPS entre 0 et 1
    # Latitude: inverser car l'image commence en haut (nord) et va vers le bas (sud)
    lat_normalized = (bounds["north"] - lat) / (bounds["north"] - bounds["south"])
    # Longitude: normaliser de l'ouest (gauche) vers l'est (droite)
    lon_normalized = (lon - bounds["west"]) / (bounds["east"] - bounds["west"])
    
    # Convertir en coordonnées d'image et appliquer les offsets
    x = int(lon_normalized * image_width) + offsets.get("x", 0)
    y = int(lat_normalized * image_height) + offsets.get("y", 0)
    
    # S'assurer que les coordonnées sont dans les limites de l'image
    x = max(0, min(image_width - 1, x))
    y = max(0, min(image_height - 1, y))
    
    return x, y


def generate_map_with_point(
    city: Dict,
    map_path: Optional[str] = None,
    point_radius: int = 5,
    point_color: Tuple[int, int, int] = (255, 0, 0),  # Rouge
    output_path: Optional[str] = None
) -> Optional['Image.Image']:
    """Génère une image de carte avec un point superposé pour la ville.
    
    Args:
        city: Dictionnaire de la ville avec 'gps' (lat, lon)
        map_path: Chemin vers l'image de la carte (défaut: data/map.png)
        point_radius: Rayon du point en pixels
        point_color: Couleur du point (R, G, B)
        output_path: Optionnel, chemin pour sauvegarder l'image
    
    Returns:
        PIL Image avec le point superposé, ou None en cas d'erreur
    """
    if not PIL_AVAILABLE:
        return None
    
    # Déterminer le chemin de la carte
    if map_path is None:
        project_root = Path(__file__).parent.parent.parent
        map_path = project_root / 'data' / 'map.png'
    else:
        map_path = Path(map_path)
    
    if not map_path.exists():
        return None
    
    try:
        # Charger l'image de la carte
        img = Image.open(map_path)
        
        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculer les coordonnées du point
        gps = city.get('gps', {})
        if not gps.get('lat') or not gps.get('lon'):
            return None
        
        width, height = img.size
        bounds, offsets = load_mapping_config()
        x, y = gps_to_image_coords(
            gps['lat'], gps['lon'], width, height, bounds=bounds, offsets=offsets
        )
        
        # Dessiner le point
        draw = ImageDraw.Draw(img)
        # Dessiner un cercle plein
        bbox = [
            x - point_radius,
            y - point_radius,
            x + point_radius,
            y + point_radius
        ]
        draw.ellipse(bbox, fill=point_color)
        
        # Optionnel: dessiner un contour blanc pour plus de visibilité
        if point_radius > 3:
            draw.ellipse(bbox, outline=(255, 255, 255), width=1)
        
        # Sauvegarder si demandé
        if output_path:
            img.save(output_path)
        
        return img
    
    except Exception as e:
        print(f"Erreur lors de la génération de la carte: {e}")
        return None

