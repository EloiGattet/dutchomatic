"""Formatting functions for exercises and answers."""

import os
import json
import tempfile
import socket
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional

from .ticket_templates import TicketTemplateManager
from .city_utils import generate_map_with_point
from .weather import get_weather, format_weather_line


TICKET_WIDTH = 58
template_manager = TicketTemplateManager()

# Caractères accentués supportés par l'imprimante (à garder)
SUPPORTED_ACCENTS = {'à', 'é', 'è', 'ç', 'À', 'É', 'È', 'Ç'}

# Mapping des caractères accentués vers leurs équivalents sans accent
ACCENT_REPLACEMENTS = {
    'â': 'a', 'Â': 'A',
    'ä': 'a', 'Ä': 'A',
    'ê': 'e', 'Ê': 'E',
    'ë': 'e', 'Ë': 'E',
    'î': 'i', 'Î': 'I',
    'ï': 'i', 'Ï': 'I',
    'ô': 'o', 'Ô': 'O',
    'ö': 'o', 'Ö': 'O',
    'ù': 'u', 'Ù': 'U',
    'û': 'u', 'Û': 'U',
    'ü': 'u', 'Ü': 'U',
    'ÿ': 'y', 'Ÿ': 'Y',
    'ñ': 'n', 'Ñ': 'N',
    'æ': 'ae', 'Æ': 'AE',
    'œ': 'oe', 'Œ': 'OE',
}


def _normalize_accents(text: str) -> str:
    """Normalise les accents pour l'imprimante.
    
    Garde uniquement à, é, è, ç et remplace tous les autres accents
    par leurs équivalents sans accent.
    
    Args:
        text: Texte à normaliser
    
    Returns:
        Texte normalisé
    """
    if not text:
        return text
    
    result = []
    for char in text:
        if char in SUPPORTED_ACCENTS:
            # Garder les accents supportés (à, é, è, ç)
            result.append(char)
        elif char in ACCENT_REPLACEMENTS:
            # Remplacer les autres accents
            result.append(ACCENT_REPLACEMENTS[char])
        else:
            # Garder les autres caractères
            result.append(char)
    
    return ''.join(result)


def _load_instagram_accounts() -> list:
    """Charge la liste des comptes Instagram depuis instagram_accounts.json."""
    project_root = Path(__file__).parent.parent.parent
    instagram_path = project_root / 'data' / 'instagram_accounts.json'
    
    if not instagram_path.exists():
        return []
    
    try:
        with open(instagram_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('categories', [])
    except Exception:
        return []


def _calculate_days_until_trip(trip_date_str: Optional[str]) -> Optional[int]:
    """Calcule le nombre de jours jusqu'au voyage."""
    if not trip_date_str:
        return None
    
    try:
        trip_date = datetime.strptime(trip_date_str, '%Y-%m-%d').date()
        today = date.today()
        delta = (trip_date - today).days
        return delta if delta >= 0 else None
    except Exception:
        return None


def _center_text(text: str, width: int) -> str:
    """Center text within width, wrap to multiple lines if too long.
    
    Returns a single string with newlines if text is too long.
    """
    text = _normalize_accents(text.strip())
    if len(text) <= width:
        # Texte court, centrer normalement
        padding = (width - len(text)) // 2
        return ' ' * padding + text + ' ' * (width - len(text) - padding)
    else:
        # Texte long, wrapper sur plusieurs lignes
        wrapped_lines = []
        words = text.split()
        current_line = ''
        for word in words:
            test_line = current_line + (' ' if current_line else '') + word
            if len(test_line) <= width:
                current_line = test_line
            else:
                if current_line:
                    # Centrer la ligne actuelle
                    padding = (width - len(current_line)) // 2
                    wrapped_lines.append(' ' * padding + current_line + ' ' * (width - len(current_line) - padding))
                current_line = word
        # Dernière ligne
        if current_line:
            padding = (width - len(current_line)) // 2
            wrapped_lines.append(' ' * padding + current_line + ' ' * (width - len(current_line) - padding))
        return '\n'.join(wrapped_lines)


def _center_text_lines(lines: list, text: str, width: int) -> None:
    """Center text and append to lines list, wrapping if too long.
    
    Args:
        lines: List to append wrapped lines to
        text: Text to center and wrap
        width: Maximum line width
    """
    centered = _center_text(text, width)
    for line in centered.split('\n'):
        lines.append(line)


def _wrap_text(lines: list, text: str, width: int, indent: str = '') -> None:
    """Wrap text to multiple lines and append to lines list.
    
    Args:
        lines: List to append wrapped lines to
        text: Text to wrap
        width: Maximum line width (without indent)
        indent: Optional indent string to prepend to each line
    """
    text = _normalize_accents(text)
    words = text.split()
    current_line = indent
    for word in words:
        test_line = current_line + (' ' if current_line != indent else '') + word
        if len(test_line) <= width + len(indent):
            current_line = test_line
        else:
            if current_line != indent:
                lines.append(current_line)
            current_line = indent + word
    if current_line != indent:
        lines.append(current_line)


def _format_box(title: str, width: int = TICKET_WIDTH) -> str:
    """Format a boxed title with visible separators.
    
    Utilise des séparateurs simples (_) au lieu de caractères Unicode de boîte
    pour une meilleure visibilité sur imprimantes thermiques.
    Le titre est wrappé sur plusieurs lignes si trop long.
    """
    # Créer un titre avec séparateurs visibles
    separator = '_' * width
    centered_title = _center_text(title, width)
    
    return f"{separator}\n{centered_title}\n{separator}"


def _get_current_date() -> Optional[str]:
    """Récupère la date du jour au format néerlandais (si connecté à internet).
    
    Returns:
        Date formatée en néerlandais (ex: "15 januari 2025") ou None si hors ligne
    """
    # Vérifier la connexion internet
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
    except OSError:
        # Pas de connexion internet
        return None
    
    try:
        # Mois en néerlandais
        months_nl = [
            'januari', 'februari', 'maart', 'april', 'mei', 'juni',
            'juli', 'augustus', 'september', 'oktober', 'november', 'december'
        ]
        
        today = date.today()
        day = today.day
        month = months_nl[today.month - 1]
        year = today.year
        
        return f"{day} {month} {year}"
    except Exception:
        return None


def _format_custom_text(text: str, exercise: Dict, daily: Optional[Dict] = None, city: Optional[Dict] = None) -> str:
    """Format custom text with variable substitution."""
    if not text:
        return ''
    
    replacements = {
        '{title}': exercise.get('title', ''),
        '{niveau}': exercise.get('niveau', ''),
        '{type}': exercise.get('type', ''),
        '{prompt}': exercise.get('prompt', ''),
    }
    
    # Ajouter la date du jour (si connecté)
    current_date = _get_current_date()
    if current_date:
        replacements['{date}'] = current_date
    else:
        replacements['{date}'] = ''  # Vide si hors ligne
    
    if daily:
        replacements['{daily_nl}'] = daily.get('nl', '')
        replacements['{daily_fr}'] = daily.get('fr', '')
    
    if city:
        replacements['{city_name}'] = city.get('name', '')
        replacements['{city_anecdote}'] = city.get('anecdote', '')
        replacements['{city_place}'] = city.get('place_to_visit', '')
    
    result = text
    for key, value in replacements.items():
        result = result.replace(key, str(value))
    
    return result


def format_exercise(exercise: Dict, daily: Optional[Dict] = None, city: Optional[Dict] = None, course: Optional[Dict] = None, template_id: Optional[str] = None, state: Optional[Dict] = None) -> tuple[str, list[str], list[str], list[str], Optional[str]]:
    """Format exercise for printing.
    
    Args:
        exercise: Exercise dict
        daily: Optional daily item dict
        city: Optional city dict for "ville du jour"
        course: Optional course dict for "cours du jour"
        template_id: Optional template ID to use (default: active template)
        state: Optional state dict for countdown and footer
    
    Returns:
        Tuple of (formatted ASCII string, list of header image paths, list of bonus image paths, list of city image paths, Instagram category name or None)
    """
    # Get template
    if template_id:
        template = template_manager.get_template(template_id)
    else:
        template = template_manager.get_active_template('exercise')
    
    # Fallback to default if no template
    if not template:
        template = {
            'header': {'image': None, 'custom_text': None},
            'content': {
                'show_title': True,
                'show_niveau': True,
                'show_prompt': True,
                'max_items': None,
                'item_format': 'numbered'
            },
            'footer': {'image': None, 'custom_text': None}
        }
    
    lines = []
    header_images = []
    bonus_images = []
    city_images = []
    instagram_category = None
    
    # Header image
    header_image = template.get('header', {}).get('image')
    if header_image:
        # Try data/ first, then web/static/images/
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        data_image = project_root / 'data' / header_image
        web_image = project_root / 'src' / 'web' / 'static' / 'images' / header_image
        
        if data_image.exists():
            header_images.append(str(data_image.relative_to(project_root)))
        elif web_image.exists():
            header_images.append(str(web_image.relative_to(project_root)))
        else:
            # Try direct path
            header_images.append(header_image)
    
    # Default logo if no header image specified
    if not header_images:
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        # Try data/ first, then web/static/images/
        default_logo_data = project_root / 'data' / 'logo_print.png'
        default_logo_web = project_root / 'src' / 'web' / 'static' / 'images' / 'logo_print.png'
        
        if default_logo_data.exists():
            header_images.append(str(default_logo_data.relative_to(project_root)))
        elif default_logo_web.exists():
            header_images.append(str(default_logo_web.relative_to(project_root)))
    
    # Date et message de bienvenue (après le logo)
    current_date = _get_current_date()
    if current_date:
        _center_text_lines(lines, current_date, TICKET_WIDTH)
    if state:
        import random
        # Utiliser encouragement_messages pour le message de bienvenue
        messages = state.get('encouragement_messages', ['Welkom!', 'Goed gedaan!', 'Veel succes!'])
        if messages:
            welcome_msg = random.choice(messages)
            _center_text_lines(lines, welcome_msg, TICKET_WIDTH)
    
    # Séparateur avant la section EXERCICE
    if template.get('content', {}).get('show_title', True):
        lines.append('_' * TICKET_WIDTH)
    
    # Title (if enabled) - format compact
    if template.get('content', {}).get('show_title', True):
        if template.get('content', {}).get('show_niveau', True):
            title = f"EXERCICE — {exercise.get('title', '')} ({exercise.get('niveau', '')})"
        else:
            title = f"EXERCICE — {exercise.get('title', '')}"
        _center_text_lines(lines, title, TICKET_WIDTH)
    
    # Prompt (if enabled)
    if template.get('content', {}).get('show_prompt', True):
        prompt = exercise.get('prompt', '')
        if prompt:
            lines.append(_normalize_accents(prompt))
    
    # Items
    items = exercise.get('items', [])
    max_items = template.get('content', {}).get('max_items')
    if max_items:
        items = items[:max_items]
    
    item_format = template.get('content', {}).get('item_format', 'numbered')
    
    for i, item in enumerate(items, 1):
        question_nl = item.get('question_nl', '')
        question_fr = item.get('question_fr', '')
        img = item.get('img', '')
        
        # Wrapper la question néerlandaise si trop longue
        prefix = f"{i}. " if item_format == 'numbered' else ("- " if item_format == 'bulleted' else "")
        prefix_len = len(prefix)
        available_width = TICKET_WIDTH - prefix_len
        
        # Construire la ligne avec préfixe (normaliser les accents)
        full_question = _normalize_accents(question_nl)
        if img:
            full_question += f" {img}"
        
        if len(full_question) <= available_width:
            # Question courte
            lines.append(prefix + full_question)
        else:
            # Question longue, wrapper
            words = full_question.split()
            current_line = prefix
            for word in words:
                test_line = current_line + (' ' if current_line != prefix else '') + word
                if len(test_line) <= TICKET_WIDTH:
                    current_line = test_line
                else:
                    if current_line != prefix:
                        lines.append(current_line)
                    # Lignes suivantes avec indentation
                    indent = ' ' * prefix_len
                    current_line = indent + word
            if current_line != prefix:
                lines.append(current_line)
        
        if question_fr:
            # Wrapper la traduction française si trop longue (normaliser les accents)
            question_fr_normalized = _normalize_accents(question_fr)
            if len(question_fr_normalized) <= TICKET_WIDTH - 3:
                lines.append(f"   {question_fr_normalized}")
            else:
                _wrap_text(lines, question_fr_normalized, TICKET_WIDTH - 3, indent="   ")
    
    # Daily bonus (étendu) - format compact
    bonus_config = template.get('bonus', {})
    if daily and bonus_config.get('enabled', True):
        lines.append('_' * TICKET_WIDTH)
        _center_text_lines(lines, '🎁 PHRASE DU JOUR', TICKET_WIDTH)
        
        # Expression du jour (classique) - pour expression, fact, quote
        nl_text = daily.get('nl', '')
        fr_text = daily.get('fr', '')
        if nl_text and fr_text:
            lines.append(f"{_normalize_accents(nl_text)} → {_normalize_accents(fr_text)}")
        
        # Recette (si présente)
        recipe = daily.get('recipe', '')
        if recipe and bonus_config.get('show_recipe', True):
            lines.append('_' * TICKET_WIDTH)
            _center_text_lines(lines, '🍳 RECETTE', TICKET_WIDTH)
            _wrap_text(lines, recipe, TICKET_WIDTH)
        
        # Photo surprise (si présente et pas déjà imprimée) - dans la section bonus
        surprise_photo = daily.get('surprise_photo', '')
        if surprise_photo and bonus_config.get('show_surprise_photo', True):
            project_root = Path(__file__).parent.parent.parent
            photo_path = project_root / 'data' / 'surprise_photos' / surprise_photo
            if photo_path.exists():
                # Vérifier si la photo a déjà été imprimée
                photo_relative_path = str(photo_path.relative_to(project_root))
                printed_photos = state.get('printed_photos', []) if state else []
                
                if photo_relative_path not in printed_photos:
                    # Photo pas encore imprimée, l'ajouter
                    bonus_images.append(photo_relative_path)
                    _center_text_lines(lines, '📸 Photo surprise', TICKET_WIDTH)
        
        # Défi (si présent)
        challenge = daily.get('challenge', '')
        if challenge and bonus_config.get('show_challenge', True):
            lines.append('_' * TICKET_WIDTH)
            _center_text_lines(lines, '💪 DÉFI DU JOUR', TICKET_WIDTH)
            _wrap_text(lines, challenge, TICKET_WIDTH)
    
    # Section cours (si un cours est fourni) - format compact
    course_config = template.get('course', {})
    if course and course_config.get('enabled', True):
        lines.append('_' * TICKET_WIDTH)
        
        # Titre simplifié
        course_title = course.get('title', '')
        course_type = course.get('type', '')
        if course_title:
            _center_text_lines(lines, f"📚 {course_title.upper()}", TICKET_WIDTH)
        else:
            _center_text_lines(lines, '📚 LES VERBES COURANTS', TICKET_WIDTH)
        
        # Pour les conversations, afficher aussi la traduction néerlandaise
        if course_type == 'conversation':
            content_nl = course.get('content_nl', '')
            content_fr = course.get('content_fr', '')
            if content_nl and content_fr:
                # Afficher les deux versions côte à côte ou l'une après l'autre
                # Format: ligne NL, puis ligne FR
                for nl_line, fr_line in zip(content_nl.split('\n'), content_fr.split('\n')):
                    nl_stripped = nl_line.strip()
                    fr_stripped = fr_line.strip()
                    if nl_stripped:
                        lines.append(_normalize_accents(nl_stripped))
                    if fr_stripped:
                        lines.append(_normalize_accents(fr_stripped))
        else:
            # Pour les autres types, juste le contenu français
            content_fr = course.get('content_fr', '')
            if content_fr:
                # Le contenu français peut contenir des retours à la ligne
                # Traiter chaque ligne séparément
                for line in content_fr.split('\n'):
                    line_stripped = line.strip()
                    if line_stripped:
                        normalized = _normalize_accents(line_stripped)
                        # Si c'est une ligne avec = (exemple: "lopen = marcher"), pas de wrap, juste l'ajouter
                        if '=' in normalized:
                            lines.append(normalized)
                        else:
                            # Sinon wrapper si nécessaire
                            _wrap_text(lines, normalized, TICKET_WIDTH)
    
    # Ville du jour - format compact, carte dans cette section
    city_config = template.get('city', {})
    if city and city_config.get('enabled', True):
        lines.append('_' * TICKET_WIDTH)
        _center_text_lines(lines, '🏙️  VILLE DU JOUR', TICKET_WIDTH)
        
        # Nom de la ville
        city_name = city.get('name', '')
        if city_name:
            _center_text_lines(lines, city_name.upper(), TICKET_WIDTH)
        
        # Météo (si activée et connecté)
        if city_config.get('show_weather', True):
            weather = get_weather(city)
            if weather:
                weather_line = format_weather_line(weather)
                _center_text_lines(lines, weather_line, TICKET_WIDTH)
        
        # Générer la carte avec le point (si activée) - dans cette section, pas dans header
        if city_config.get('show_map', True):
            project_root = Path(__file__).parent.parent.parent
            temp_dir = project_root / 'output' / 'temp'
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Créer un fichier temporaire pour la carte
            temp_map_path = temp_dir / f"city_map_{city.get('id', 'unknown')}.png"
            map_img = generate_map_with_point(city, output_path=str(temp_map_path))
            
            if map_img and temp_map_path.exists():
                # La carte va dans city_images, pas header_images
                city_images.append(str(temp_map_path.relative_to(project_root)))
        
        # Anecdote - format compact, juste émoji, pas de saut de ligne
        anecdote = city.get('anecdote', '')
        if anecdote:
            normalized_anecdote = _normalize_accents(anecdote)
            # Si vraiment trop long (>80), tronquer
            if len(normalized_anecdote) > 80:
                normalized_anecdote = normalized_anecdote[:77] + '...'
            lines.append('💡 ' + normalized_anecdote)
        
        # Lieu à visiter - format compact, pas de saut de ligne
        place = city.get('place_to_visit', '')
        if place:
            lines.append('📍 À VISITER')
            # Pas de wrap, mettre tout sur une ligne (l'imprimante gérera si nécessaire)
            normalized_place = _normalize_accents(place)
            # Si vraiment trop long (>80), tronquer
            if len(normalized_place) > 80:
                normalized_place = normalized_place[:77] + '...'
            lines.append(normalized_place)
    
    # Comptes Instagram (si activé) - format compact, un seul compte, avec trace
    instagram_config = template.get('instagram', {})
    if instagram_config.get('enabled', False):
        instagram_categories = _load_instagram_accounts()
        if instagram_categories:
            lines.append('_' * TICKET_WIDTH)
            _center_text_lines(lines, '📱 COMPTES À SUIVRE', TICKET_WIDTH)
            
            # Récupérer les comptes déjà affichés depuis le state
            printed_accounts = state.get('printed_instagram_accounts', []) if state else []
            
            # Filtrer les catégories pour exclure celles déjà affichées
            available_categories = [
                cat for cat in instagram_categories
                if cat.get('name', '') not in printed_accounts
            ]
            
            # Si toutes les catégories ont été affichées, réinitialiser
            if not available_categories:
                available_categories = instagram_categories
                printed_accounts = []
            
            # Afficher une catégorie aléatoire parmi celles disponibles
            import random
            selected_category = random.choice(available_categories)
            category_name = selected_category.get('name', '')
            accounts = selected_category.get('accounts', [])
            
            if category_name and accounts:
                # Juste le nom de catégorie, pas de séparateur
                lines.append(category_name)
                
                # Un seul compte
                account = accounts[0] if accounts else None
                if account:
                    handle = account.get('handle', '')
                    theme = account.get('theme', '')
                    why = account.get('why', '')
                    
                    if handle and theme:
                        lines.append(f"{_normalize_accents(handle)} : {_normalize_accents(theme)}")
                    elif handle:
                        lines.append(_normalize_accents(handle))
                    if why:
                        # Pas de wrap pour le "why", mettre sur une ligne
                        normalized_why = _normalize_accents(why)
                        if len(normalized_why) > 80:
                            normalized_why = normalized_why[:77] + '...'
                        lines.append(f"→ {normalized_why}")
                
                # Marquer cette catégorie pour sauvegarde dans state_manager
                instagram_category = category_name
    
    # Countdown voyage (si activé) - format compact
    countdown_config = template.get('countdown', {})
    if countdown_config.get('enabled', False) and state:
        trip_date = state.get('trip_date')
        days_left = _calculate_days_until_trip(trip_date)
        if days_left is not None:
            lines.append('_' * TICKET_WIDTH)
            _center_text_lines(lines, '✈️  COUNTDOWN VOYAGE', TICKET_WIDTH)
            _center_text_lines(lines, f"Plus que {days_left} jour{'s' if days_left > 1 else ''} avant les Pays-Bas !", TICKET_WIDTH)
    
    # Footer custom text
    if template.get('footer', {}).get('custom_text'):
        footer_text = _format_custom_text(
            template['footer']['custom_text'],
            exercise,
            daily,
            city
        )
        if footer_text:
            lines.append(_normalize_accents(footer_text))
    
    # Footer amélioré (message d'encouragement + compteur) - format compact
    footer_config = template.get('footer', {})
    if footer_config.get('show_encouragement', True) or footer_config.get('show_counter', True):
        lines.append('_' * TICKET_WIDTH)
        
        # Message d'encouragement
        if footer_config.get('show_encouragement', True) and state:
            import random
            messages = state.get('encouragement_messages', [])
            if messages:
                message = random.choice(messages)
                _center_text_lines(lines, message, TICKET_WIDTH)
        
        # Compteur de progression
        if footer_config.get('show_counter', True) and state:
            compteur = state.get('compteur_total', 0)
            _center_text_lines(lines, f"Ticket n°{compteur}", TICKET_WIDTH)
        
        lines.append('_' * TICKET_WIDTH)
    
    return '\n'.join(lines), header_images, bonus_images, city_images, instagram_category


def format_answers(exercise: Dict, template_id: Optional[str] = None) -> tuple[str, list[str]]:
    """Format answers for printing.
    
    Args:
        exercise: Exercise dict
        template_id: Optional template ID to use (default: active template)
    
    Returns:
        Tuple of (formatted ASCII string, list of image paths to print before text)
    """
    # Get template
    if template_id:
        template = template_manager.get_template(template_id)
    else:
        template = template_manager.get_active_template('answers')
    
    # Fallback to default if no template
    if not template:
        template = {
            'header': {'image': None, 'custom_text': None},
            'content': {
                'show_title': True,
                'show_niveau': True,
                'max_items': None,
                'item_format': 'numbered'
            },
            'footer': {'image': None, 'custom_text': None}
        }
    
    lines = []
    header_images = []
    
    # Header image
    header_image = template.get('header', {}).get('image')
    if header_image:
        # Try data/ first, then web/static/images/
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        data_image = project_root / 'data' / header_image
        web_image = project_root / 'src' / 'web' / 'static' / 'images' / header_image
        
        if data_image.exists():
            header_images.append(str(data_image.relative_to(project_root)))
        elif web_image.exists():
            header_images.append(str(web_image.relative_to(project_root)))
        else:
            # Try direct path
            header_images.append(header_image)
    
    # Header custom text
    if template.get('header', {}).get('custom_text'):
        header_text = _format_custom_text(
            template['header']['custom_text'],
            exercise
        )
        if header_text:
            lines.append(_normalize_accents(header_text))
            lines.append('')
    
    # Title box (if enabled)
    if template.get('content', {}).get('show_title', True):
        if template.get('content', {}).get('show_niveau', True):
            title = f"CORRECTIONS — {exercise.get('title', '')} ({exercise.get('niveau', '')})"
        else:
            title = f"CORRECTIONS — {exercise.get('title', '')}"
        lines.append(_format_box(title))
        lines.append('')
    
    # Items with answers
    items = exercise.get('items', [])
    max_items = template.get('content', {}).get('max_items')
    if max_items:
        items = items[:max_items]
    
    item_format = template.get('content', {}).get('item_format', 'numbered')
    
    for i, item in enumerate(items, 1):
        question_nl = item.get('question_nl', '')
        question_fr = item.get('question_fr', '')
        answer = item.get('answer', '')
        img = item.get('img', '')
        
        # Normaliser les accents
        question_nl = _normalize_accents(question_nl)
        question_fr = _normalize_accents(question_fr) if question_fr else ''
        answer = _normalize_accents(answer) if answer else ''
        
        if item_format == 'numbered':
            lines.append(f"{i}. {question_nl}")
        elif item_format == 'bulleted':
            lines.append(f"- {question_nl}")
        else:  # plain
            lines.append(question_nl)
        
        if img:
            lines.append(f"   {img}")
        if question_fr:
            lines.append(f"   {question_fr}")
        if answer:
            lines.append(f"   ✓ {answer}")
        lines.append('')
    
    # Explanations
    explanations = exercise.get('explanations', '')
    if explanations:
        lines.append('_' * TICKET_WIDTH)
        lines.append('📝 EXPLICATIONS')
        lines.append(_normalize_accents(explanations))
        lines.append('_' * TICKET_WIDTH)
    
    # Footer custom text
    if template.get('footer', {}).get('custom_text'):
        footer_text = _format_custom_text(
            template['footer']['custom_text'],
            exercise
        )
        if footer_text:
            lines.append('')
            lines.append(_normalize_accents(footer_text))
    
    return '\n'.join(lines), header_images
