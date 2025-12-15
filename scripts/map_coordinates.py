#!/usr/bin/env python3
"""Utilitaire pour mapper les coordonnées GPS aux coordonnées de l'image PNG.

Cet utilitaire permet de :
1. Charger une carte PNG
2. Entrer les coordonnées GPS d'une ville
3. Calculer et afficher les coordonnées (x, y) correspondantes sur l'image
4. Mettre à jour automatiquement le fichier cities.json avec les coordonnées calculées
"""

import json
import sys
from pathlib import Path
from typing import Tuple, Optional, List

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Erreur: PIL/Pillow n'est pas installé. Installez-le avec: pip install Pillow")
    sys.exit(1)


# Bornes GPS des Pays-Bas (valeurs optimales calibrées)
# Ces valeurs définissent les limites de la carte
DEFAULT_BOUNDS = {
    "north": 53.750000,  # Latitude maximale (nord)
    "south": 50.520000,  # Latitude minimale (sud)
    "east": 7.227500,    # Longitude maximale (est)
    "west": 3.150000     # Longitude minimale (ouest)
}

# Offsets pour décaler les points (en pixels)
DEFAULT_OFFSETS = {
    "x": 0,  # Décalage horizontal
    "y": 0   # Décalage vertical
}


def load_mapping_config() -> Tuple[dict, dict]:
    """Charge la configuration de mapping depuis un fichier JSON.
    
    Returns:
        Tuple (bounds, offsets)
    """
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'config' / 'map_mapping.json'
    
    bounds = DEFAULT_BOUNDS.copy()
    offsets = DEFAULT_OFFSETS.copy()
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                bounds.update(config.get('bounds', {}))
                offsets.update(config.get('offsets', {}))
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement de la config: {e}")
    
    return bounds, offsets


def save_mapping_config(bounds: dict, offsets: dict) -> bool:
    """Sauvegarde la configuration de mapping dans un fichier JSON.
    
    Args:
        bounds: Dictionnaire avec 'north', 'south', 'east', 'west'
        offsets: Dictionnaire avec 'x', 'y'
    
    Returns:
        True si succès
    """
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'config' / 'map_mapping.json'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config = {
            'bounds': bounds,
            'offsets': offsets
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuration sauvegardée: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False


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
    
    # Convertir en coordonnées d'image
    x = int(lon_normalized * image_width) + offsets.get("x", 0)
    y = int(lat_normalized * image_height) + offsets.get("y", 0)
    
    # S'assurer que les coordonnées sont dans les limites de l'image
    x = max(0, min(image_width - 1, x))
    y = max(0, min(image_height - 1, y))
    
    return x, y


def load_cities() -> list:
    """Charge la liste des villes depuis cities.json."""
    project_root = Path(__file__).parent.parent
    cities_path = project_root / 'data' / 'cities.json'
    
    if not cities_path.exists():
        print(f"Erreur: {cities_path} n'existe pas")
        return []
    
    with open(cities_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_cities(cities: list) -> bool:
    """Sauvegarde la liste des villes dans cities.json."""
    project_root = Path(__file__).parent.parent
    cities_path = project_root / 'data' / 'cities.json'
    
    try:
        with open(cities_path, 'w', encoding='utf-8') as f:
            json.dump(cities, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False


def calculate_bounds_adjustment(
    city_gps: dict,
    error_x: int,
    error_y: int,
    image_width: int,
    image_height: int,
    current_bounds: dict
) -> dict:
    """Calcule les ajustements recommandés pour les bornes GPS basés sur une erreur observée.
    
    Args:
        city_gps: Dictionnaire avec 'lat' et 'lon' de la ville
        error_x: Erreur en pixels sur X (positif = trop à droite, négatif = trop à gauche)
        error_y: Erreur en pixels sur Y (positif = trop bas, négatif = trop haut)
        image_width: Largeur de l'image
        image_height: Hauteur de l'image
        current_bounds: Bornes GPS actuelles
    
    Returns:
        Dictionnaire avec les ajustements recommandés pour les bornes
    """
    # Calculer les ajustements en degrés GPS
    # Pour X (longitude) : error_x pixels = error_x / image_width * (east - west) degrés
    lon_range = current_bounds['east'] - current_bounds['west']
    lat_range = current_bounds['north'] - current_bounds['south']
    
    # Ajustement en degrés
    # Si error_x > 0 (trop à droite), il faut réduire la plage de longitude
    # On peut soit réduire east, soit augmenter west, ou les deux
    lon_adjustment_per_pixel = lon_range / image_width
    lat_adjustment_per_pixel = lat_range / image_height
    
    lon_adjustment = -error_x * lon_adjustment_per_pixel  # Négatif car si trop à droite, il faut réduire east
    lat_adjustment = error_y * lat_adjustment_per_pixel   # Positif car si trop bas, il faut augmenter south
    
    return {
        'east_adjustment': lon_adjustment,   # Réduire east si error_x > 0
        'west_adjustment': 0,  # On ajuste seulement east pour X
        'south_adjustment': lat_adjustment,  # Augmenter south si error_y > 0
        'north_adjustment': 0  # On ajuste seulement south pour Y
    }


def calculate_optimal_adjustment_from_corrections(
    corrections: list,
    image_width: int,
    image_height: int,
    current_bounds: dict
) -> dict:
    """Calcule un ajustement optimal basé sur plusieurs corrections.
    
    Args:
        corrections: Liste de dict avec 'city_id', 'error_x', 'error_y'
        image_width: Largeur de l'image
        image_height: Hauteur de l'image
        current_bounds: Bornes GPS actuelles
    
    Returns:
        Dictionnaire avec les ajustements moyens recommandés
    """
    cities = load_cities()
    city_map = {c['id']: c for c in cities}
    
    adjustments = {
        'east_adjustment': [],
        'south_adjustment': []
    }
    
    for correction in corrections:
        city_id = correction['city_id']
        if city_id not in city_map:
            continue
        
        city = city_map[city_id]
        gps = city.get('gps', {})
        if not gps.get('lat') or not gps.get('lon'):
            continue
        
        adj = calculate_bounds_adjustment(
            gps,
            correction['error_x'],
            correction['error_y'],
            image_width,
            image_height,
            current_bounds
        )
        
        adjustments['east_adjustment'].append(adj['east_adjustment'])
        adjustments['south_adjustment'].append(adj['south_adjustment'])
    
    # Calculer la moyenne
    result = {
        'east_adjustment': sum(adjustments['east_adjustment']) / len(adjustments['east_adjustment']) if adjustments['east_adjustment'] else 0,
        'west_adjustment': 0,
        'south_adjustment': sum(adjustments['south_adjustment']) / len(adjustments['south_adjustment']) if adjustments['south_adjustment'] else 0,
        'north_adjustment': 0
    }
    
    return result


def calculate_city_coords(city_id: str, image_width: int, image_height: int) -> Optional[Tuple[int, int]]:
    """Calcule les coordonnées d'une ville à partir de son GPS."""
    cities = load_cities()
    
    city = next((c for c in cities if c.get('id') == city_id), None)
    if not city:
        print(f"Ville '{city_id}' non trouvée")
        return None
    
    gps = city.get('gps', {})
    if not gps.get('lat') or not gps.get('lon'):
        print(f"Coordonnées GPS manquantes pour {city['name']}")
        return None
    
    return gps_to_image_coords(gps['lat'], gps['lon'], image_width, image_height)


def draw_cities_on_map(img: Image.Image, cities: list, show_labels: bool = True, bounds: dict = None, offsets: dict = None) -> Image.Image:
    """Dessine tous les points des villes sur la carte.
    
    Args:
        img: Image PIL de la carte
        cities: Liste des villes
        show_labels: Si True, affiche les noms des villes
    
    Returns:
        Image avec les points dessinés
    """
    # Créer une copie pour ne pas modifier l'original
    img = img.copy()
    
    # Convertir en RGB si nécessaire
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Couleurs
    point_color = (255, 0, 0)  # Rouge
    outline_color = (255, 255, 255)  # Blanc
    text_color = (0, 0, 0)  # Noir
    text_bg = (255, 255, 255)  # Blanc pour le fond du texte
    
    # Dessiner les points pour chaque ville
    for city in cities:
        gps = city.get('gps', {})
        if not gps.get('lat') or not gps.get('lon'):
            continue
        
        # Calculer les coordonnées
        x, y = gps_to_image_coords(gps['lat'], gps['lon'], width, height, bounds=bounds, offsets=offsets)
        
        # Dessiner le point (cercle)
        point_radius = 6
        bbox = [
            x - point_radius,
            y - point_radius,
            x + point_radius,
            y + point_radius
        ]
        draw.ellipse(bbox, fill=point_color, outline=outline_color, width=2)
        
        # Afficher le nom de la ville si demandé
        if show_labels:
            city_name = city.get('name', '')
            if city_name:
                # Position du texte (à droite du point)
                text_x = x + point_radius + 5
                text_y = y - 8
                
                # Essayer de charger une police, sinon utiliser la police par défaut
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
                
                # Estimation de la taille du texte
                if font:
                    try:
                        # Nouvelle API (PIL 9.0+)
                        bbox_text = draw.textbbox((text_x, text_y), city_name, font=font)
                    except AttributeError:
                        # Ancienne API (PIL < 9.0)
                        text_width, text_height = draw.textsize(city_name, font=font)
                        bbox_text = (text_x, text_y, text_x + text_width, text_y + text_height)
                else:
                    # Estimation si pas de font
                    text_width = len(city_name) * 6
                    text_height = 12
                    bbox_text = (text_x, text_y, text_x + text_width, text_y + text_height)
                
                # Rectangle avec padding
                padding = 2
                bg_box = (
                    bbox_text[0] - padding,
                    bbox_text[1] - padding,
                    bbox_text[2] + padding,
                    bbox_text[3] + padding
                )
                draw.rectangle(bg_box, fill=text_bg, outline=text_color, width=1)
                
                # Dessiner le texte
                draw.text((text_x, text_y), city_name, fill=text_color, font=font)
    
    return img


def show_map_with_cities(cities: list, output_path: Optional[str] = None, bounds: dict = None, offsets: dict = None) -> bool:
    """Affiche la carte avec tous les points des villes.
    
    Args:
        cities: Liste des villes
        output_path: Optionnel, chemin pour sauvegarder l'image
        bounds: Optionnel, bornes GPS personnalisées
        offsets: Optionnel, offsets personnalisés
    
    Returns:
        True si succès
    """
    project_root = Path(__file__).parent.parent
    map_path = project_root / 'data' / 'map.png'
    
    if not map_path.exists():
        print(f"Erreur: {map_path} n'existe pas")
        return False
    
    try:
        # Charger l'image
        img = Image.open(map_path)
        
        # Dessiner les villes
        img_with_cities = draw_cities_on_map(img, cities, show_labels=True, bounds=bounds, offsets=offsets)
        
        # Sauvegarder si demandé
        if output_path:
            img_with_cities.save(output_path)
            print(f"✅ Carte sauvegardée: {output_path}")
        
        # Afficher la carte
        print("🖼️  Ouverture de la carte avec les villes...")
        img_with_cities.show()
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def interactive_mode():
    """Mode interactif pour ajuster le mapping des coordonnées."""
    project_root = Path(__file__).parent.parent
    map_path = project_root / 'data' / 'map.png'
    
    if not map_path.exists():
        print(f"Erreur: {map_path} n'existe pas")
        return
    
    # Charger l'image
    img = Image.open(map_path)
    width, height = img.size
    print(f"\n📷 Image chargée: {width}x{height} pixels")
    
    # Charger la configuration
    bounds, offsets = load_mapping_config()
    
    # Charger les villes
    cities = load_cities()
    if not cities:
        return
    
    print("\n" + "="*60)
    print("Mode interactif - Ajustement du mapping GPS → Image")
    print("="*60)
    
    while True:
        print("\n📐 Configuration actuelle:")
        print(f"   Bornes GPS:")
        print(f"     Nord:  {bounds['north']:.6f}")
        print(f"     Sud:   {bounds['south']:.6f}")
        print(f"     Est:   {bounds['east']:.6f}")
        print(f"     Ouest: {bounds['west']:.6f}")
        print(f"   Décalages (pixels):")
        print(f"     X: {offsets['x']:+d}")
        print(f"     Y: {offsets['y']:+d}")
        
        print("\nOptions:")
        print("  1. Afficher la carte avec tous les points des villes")
        print("  2. Ajuster les bornes GPS (échelle)")
        print("  3. Ajuster les décalages (offset X, Y)")
        print("  4. Corriger une ville spécifique (calcule les ajustements)")
        print("  5. Réinitialiser aux valeurs par défaut")
        print("  6. Sauvegarder la configuration")
        print("  7. Afficher les coordonnées calculées")
        print("  8. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        if choice == '1':
            # Afficher la carte avec les villes
            show_map_with_cities(cities, bounds=bounds, offsets=offsets)
        
        elif choice == '2':
            # Ajuster les bornes GPS
            print("\n📐 Ajustement des bornes GPS (appuyez sur Entrée pour garder la valeur actuelle)")
            try:
                north = input(f"  Nord (actuel: {bounds['north']:.6f}): ").strip()
                if north:
                    bounds['north'] = float(north)
                
                south = input(f"  Sud (actuel: {bounds['south']:.6f}): ").strip()
                if south:
                    bounds['south'] = float(south)
                
                east = input(f"  Est (actuel: {bounds['east']:.6f}): ").strip()
                if east:
                    bounds['east'] = float(east)
                
                west = input(f"  Ouest (actuel: {bounds['west']:.6f}): ").strip()
                if west:
                    bounds['west'] = float(west)
                
                print("✅ Bornes GPS mises à jour")
                print("💡 Utilisez l'option 1 pour voir le résultat")
            except ValueError:
                print("❌ Valeurs invalides")
        
        elif choice == '3':
            # Ajuster les décalages
            print("\n📐 Ajustement des décalages (en pixels, appuyez sur Entrée pour garder la valeur actuelle)")
            try:
                offset_x = input(f"  Décalage X (actuel: {offsets['x']:+d}): ").strip()
                if offset_x:
                    offsets['x'] = int(offset_x)
                
                offset_y = input(f"  Décalage Y (actuel: {offsets['y']:+d}): ").strip()
                if offset_y:
                    offsets['y'] = int(offset_y)
                
                print("✅ Décalages mis à jour")
                print("💡 Utilisez l'option 1 pour voir le résultat")
            except ValueError:
                print("❌ Valeurs invalides")
        
        elif choice == '4':
            # Corriger une ou plusieurs villes
            print("\n🔧 Correction de villes")
            print("Vous pouvez entrer plusieurs corrections pour calculer un ajustement optimal")
            print("(Appuyez sur Entrée sans valeur pour terminer)")
            
            corrections = []
            while True:
                city_id = input("\nID de la ville (ou Entrée pour terminer): ").strip()
                if not city_id:
                    break
                
                city = next((c for c in cities if c.get('id') == city_id), None)
                if not city:
                    print(f"❌ Ville '{city_id}' non trouvée")
                    continue
                
                gps = city.get('gps', {})
                if not gps.get('lat') or not gps.get('lon'):
                    print(f"❌ Coordonnées GPS manquantes pour {city['name']}")
                    continue
                
                try:
                    error_x = int(input(f"  Erreur X pour {city['name']} (positif=trop à droite, négatif=trop à gauche): "))
                    error_y = int(input(f"  Erreur Y pour {city['name']} (positif=trop bas, négatif=trop haut): "))
                    
                    corrections.append({
                        'city_id': city_id,
                        'error_x': error_x,
                        'error_y': error_y
                    })
                    print(f"  ✓ Correction enregistrée pour {city['name']}")
                except ValueError:
                    print("❌ Valeurs invalides")
            
            if not corrections:
                print("Aucune correction enregistrée")
                continue
            
            # Calculer l'ajustement optimal
            if len(corrections) == 1:
                # Une seule correction, utiliser directement
                city = next((c for c in cities if c.get('id') == corrections[0]['city_id']), None)
                adjustments = calculate_bounds_adjustment(
                    city['gps'],
                    corrections[0]['error_x'],
                    corrections[0]['error_y'],
                    width, height, bounds
                )
            else:
                # Plusieurs corrections, calculer la moyenne
                adjustments = calculate_optimal_adjustment_from_corrections(
                    corrections, width, height, bounds
                )
            
            print(f"\n📐 Ajustements recommandés (basés sur {len(corrections)} correction(s)):")
            print(f"   Est (east):   {adjustments['east_adjustment']:+.6f} degrés")
            print(f"   Sud (south):  {adjustments['south_adjustment']:+.6f} degrés")
            
            print(f"\n💡 Nouvelles valeurs suggérées:")
            new_east = bounds['east'] + adjustments['east_adjustment']
            new_south = bounds['south'] + adjustments['south_adjustment']
            print(f"   Est:   {new_east:.6f} (actuel: {bounds['east']:.6f})")
            print(f"   Sud:   {new_south:.6f} (actuel: {bounds['south']:.6f})")
            print(f"   Ouest: {bounds['west']:.6f} (inchangé)")
            print(f"   Nord:  {bounds['north']:.6f} (inchangé)")
            
            apply = input("\n❓ Appliquer ces ajustements? (o/N): ").strip().lower()
            if apply == 'o':
                bounds['east'] = new_east
                bounds['south'] = new_south
                print("✅ Ajustements appliqués")
                print("💡 Utilisez l'option 1 pour voir le résultat")
        
        elif choice == '5':
            # Réinitialiser
            bounds = DEFAULT_BOUNDS.copy()
            offsets = DEFAULT_OFFSETS.copy()
            print("✅ Configuration réinitialisée aux valeurs par défaut")
        
        elif choice == '6':
            # Sauvegarder
            if save_mapping_config(bounds, offsets):
                print("💡 La configuration sera utilisée automatiquement lors de l'impression")
        
        elif choice == '7':
            # Afficher les coordonnées
            print("\n🔄 Coordonnées calculées pour toutes les villes:")
            for city in cities:
                gps = city.get('gps', {})
                if gps.get('lat') and gps.get('lon'):
                    x, y = gps_to_image_coords(
                        gps['lat'], gps['lon'], width, height, bounds=bounds, offsets=offsets
                    )
                    print(f"  ✓ {city['name']}: GPS({gps['lat']:.4f}, {gps['lon']:.4f}) → Image({x}, {y})")
        
        elif choice == '8':
            # Demander si on veut sauvegarder avant de quitter
            if bounds != DEFAULT_BOUNDS or offsets != DEFAULT_OFFSETS:
                save = input("\n💾 Sauvegarder la configuration avant de quitter? (o/N): ").strip().lower()
                if save == 'o':
                    save_mapping_config(bounds, offsets)
            break
        
        else:
            print("❌ Choix invalide")


def batch_mode():
    """Mode batch: calcule et affiche toutes les coordonnées, puis affiche la carte."""
    project_root = Path(__file__).parent.parent
    map_path = project_root / 'data' / 'map.png'
    
    if not map_path.exists():
        print(f"Erreur: {map_path} n'existe pas")
        return
    
    img = Image.open(map_path)
    width, height = img.size
    
    # Charger la configuration
    bounds, offsets = load_mapping_config()
    
    cities = load_cities()
    if not cities:
        return
    
    print(f"🔄 Calcul des coordonnées pour {len(cities)} villes...")
    print(f"📐 Utilisation de la configuration: bounds={bounds}, offsets={offsets}")
    
    for city in cities:
        gps = city.get('gps', {})
        if gps.get('lat') and gps.get('lon'):
            x, y = gps_to_image_coords(
                gps['lat'], gps['lon'], width, height, bounds=bounds, offsets=offsets
            )
            print(f"  ✓ {city['name']}: GPS({gps['lat']:.4f}, {gps['lon']:.4f}) → Image({x}, {y})")
    
    print("\n✅ Calcul terminé (les coordonnées sont calculées dynamiquement)")
    print("\n🖼️  Affichage de la carte avec les villes...")
    show_map_with_cities(cities, bounds=bounds, offsets=offsets)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        batch_mode()
    else:
        interactive_mode()

