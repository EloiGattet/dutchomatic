"""Preview routes for web interface."""

from flask import Blueprint, render_template, current_app
from pathlib import Path
from src.web.app import storage
from src.core.selector import select_exercise
from src.core.daily_selector import select_daily
from src.core.course_selector import select_course
from src.core.city_selector import select_city
from src.core.formatter import format_exercise

bp = Blueprint('preview', __name__, url_prefix='/preview')


def text_to_html(text: str, header_images: list, bonus_images: list, city_images: list) -> str:
    """Convert formatted text to HTML for preview."""
    lines = text.split('\n')
    html_parts = []
    
    project_root = Path(__file__).parent.parent.parent.parent
    
    def get_image_url(img_path: str) -> str:
        """Convert image path to URL."""
        full_path = project_root / img_path
        if full_path.exists():
            if img_path.startswith('data/'):
                return f"/static/data/{img_path[5:]}"
            elif img_path.startswith('src/web/static/'):
                return f"/static/{img_path[15:]}"
            elif img_path.startswith('output/'):
                return f"/static/output/{img_path[7:]}"
            else:
                return f"/static/{img_path}"
        return ""
    
    # Process header images
    for img_path in header_images:
        url_path = get_image_url(img_path)
        if url_path:
            html_parts.append(f'<div class="ticket-image"><img src="{url_path}" alt="Header" /></div>')
    
    # Process text lines and insert city images when we reach "VILLE DU JOUR" section
    in_city_section = False
    city_image_inserted = False
    city_lines_count = 0
    
    for line in lines:
        # Check if we're entering the city section
        if '🏙️' in line and 'VILLE DU JOUR' in line:
            in_city_section = True
            city_lines_count = 0
        
        # Insert city image after city name and weather (2-3 centered lines after title)
        if in_city_section and not city_image_inserted:
            stripped = line.strip()
            leading_spaces = len(line) - len(line.lstrip())
            trailing_spaces = len(line) - len(line.rstrip())
            is_centered = (
                len(stripped) < 50 and
                leading_spaces > 5 and
                abs(leading_spaces - trailing_spaces) < 5
            )
            
            if is_centered:
                city_lines_count += 1
            elif city_lines_count >= 2 and city_images:
                # Insert image after city name and weather (2+ centered lines)
                for img_path in city_images:
                    url_path = get_image_url(img_path)
                    if url_path:
                        html_parts.append(f'<div class="ticket-image"><img src="{url_path}" alt="City Map" /></div>')
                city_image_inserted = True
        
        if not line.strip():
            html_parts.append('<div class="ticket-line ticket-empty"></div>')
            continue
        
        # Check for separator lines (all underscores)
        stripped = line.strip()
        if stripped and all(c == '_' for c in stripped):
            html_parts.append('<div class="ticket-line ticket-separator"></div>')
            continue
        
        # Escape HTML special characters
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Check for centered text
        # Lines are centered if they have significant padding (spaces) on both sides
        # and the actual text is shorter than the full line width
        leading_spaces = len(line) - len(line.lstrip())
        trailing_spaces = len(line) - len(line.rstrip())
        is_centered = (
            len(stripped) < 50 and  # Short text
            leading_spaces > 5 and  # Significant leading spaces
            abs(leading_spaces - trailing_spaces) < 5  # Roughly balanced padding
        )
        
        if is_centered:
            html_parts.append(f'<div class="ticket-line ticket-centered">{escaped_line.strip()}</div>')
        else:
            # Regular line - preserve formatting but strip excessive trailing spaces
            html_parts.append(f'<div class="ticket-line">{escaped_line.rstrip()}</div>')
    
    # Process bonus images
    for img_path in bonus_images:
        url_path = get_image_url(img_path)
        if url_path:
            html_parts.append(f'<div class="ticket-image ticket-bonus"><img src="{url_path}" alt="Bonus" /></div>')
    
    return '\n'.join(html_parts)


@bp.route('/exercise')
def preview_exercise():
    """Preview a new exercise."""
    try:
        # Get state
        state = storage.get_state()
        niveau_actuel = state.get('niveau_actuel', 'A1')
        
        # Get settings for policy
        from src.web.routes.settings import load_settings
        settings = load_settings()
        policy = settings.get('draw_policy', 'strict')
        mix_ratio = settings.get('draw_mix_percent', 70) / 100.0
        
        # Select exercise
        exercise = select_exercise(
            storage,
            niveau_actuel,
            policy=policy,
            mix_ratio=mix_ratio
        )
        
        if not exercise:
            return render_template('preview_error.html', error='Aucun exercice disponible'), 404
        
        # Select daily bonus
        daily = select_daily(storage)
        
        # Select course
        course = select_course(storage)
        
        # Select city for "ville du jour"
        city = select_city()
        
        # Format exercise
        formatted_text, header_images, bonus_images, city_images, instagram_category = format_exercise(
            exercise,
            daily=daily,
            city=city,
            course=course,
            state=state
        )
        
        # Convert to HTML
        html_content = text_to_html(formatted_text, header_images, bonus_images, city_images)
        
        return render_template(
            'preview.html',
            exercise=exercise,
            html_content=html_content,
            daily=daily,
            course=course,
            city=city
        )
        
    except Exception as e:
        current_app.logger.error(f'Error previewing exercise: {str(e)}', exc_info=True)
        return render_template('preview_error.html', error=str(e)), 500

