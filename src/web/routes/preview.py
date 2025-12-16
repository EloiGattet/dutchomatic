"""Preview routes for web interface."""

from flask import Blueprint, render_template, current_app, send_file, jsonify
from pathlib import Path
from src.core.selector import select_exercise
from src.core.daily_selector import select_daily
from src.core.course_selector import select_course
from src.core.city_selector import select_city
from src.core.formatter import format_exercise
from src.core.state_manager import StateManager

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
        storage = current_app.extensions['storage']
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


@bp.route('/visual')
def preview_visual():
    """Generate visual bitmap preview using VisualSimulatorPrinter."""
    try:
        current_app.logger.info('Starting visual preview generation')
        
        storage = current_app.extensions['storage']
        # Get state
        state = storage.get_state()
        niveau_actuel = state.get('niveau_actuel', 'A1')
        current_app.logger.debug(f'State loaded: niveau_actuel={niveau_actuel}')
        
        # Get settings for policy
        from src.web.routes.settings import load_settings
        settings = load_settings()
        policy = settings.get('draw_policy', 'strict')
        mix_ratio = settings.get('draw_mix_percent', 70) / 100.0
        current_app.logger.debug(f'Settings loaded: policy={policy}, mix_ratio={mix_ratio}')
        
        # Select exercise
        current_app.logger.debug('Selecting exercise...')
        exercise = select_exercise(
            storage,
            niveau_actuel,
            policy=policy,
            mix_ratio=mix_ratio
        )
        
        if not exercise:
            current_app.logger.warning('No exercise available')
            return jsonify({
                'success': False,
                'error': 'Aucun exercice disponible'
            }), 404
        
        current_app.logger.debug(f'Exercise selected: {exercise.get("id", "unknown")}')
        
        # Select daily bonus
        current_app.logger.debug('Selecting daily bonus...')
        daily = select_daily(storage)
        
        # Select course
        current_app.logger.debug('Selecting course...')
        course = select_course(storage)
        
        # Select city for "ville du jour"
        current_app.logger.debug('Selecting city...')
        city = select_city()
        
        # Use real printer to generate ESC/POS commands, then replay in visual simulator
        try:
            current_app.logger.debug('Importing printers...')
            from src.printer.visual_simulator import VisualSimulatorPrinter
            from src.printer.escpos import EscposPrinter
            from src.printer.printer import get_printer
            
            # Get config
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'printer.json'
            current_app.logger.debug(f'Project root: {project_root}')
            
            # Load printer config
            import json
            config = {
                'type': 'escpos',
                'device': '/dev/null',
                'width': 58,
                'width_px': 384,
                'codepage': 'gb18030',
                'international': 'FRANCE',
                'default_encoding': 'gb18030'
            }
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
            
            # Create a command-capturing printer class
            captured_commands = []
            
            class CommandCapturePrinter(EscposPrinter):
                """Printer that captures all ESC/POS commands without actually printing."""
                def _init_printer(self, codepage: str, international: str) -> None:
                    """Override: don't connect to serial, just simulate initialization."""
                    # Don't connect to serial, but set _ser to a dummy object so print_text() works
                    class DummySerial:
                        pass
                    self._ser = DummySerial()
                    # Simulate initialization commands
                    self.reset()
                    self.set_international(international)
                    self.set_codepage(codepage)
                    self.set_heating(n1=7, n2=180, n3=2)
                    self.set_density(density=15, breaktime=0)
                
                def raw(self, data: bytes, description: str = "") -> None:
                    """Override: capture command instead of sending to serial."""
                    captured_commands.append((data, description))
            
            # Create real printer to capture commands
            current_app.logger.debug('Creating command-capturing printer...')
            real_printer = CommandCapturePrinter(
                device='/dev/null',  # Won't actually connect
                width=config.get('width', 58),
                baudrate=9600,
                timeout=1,
                width_px=config.get('width_px', 384),
                default_encoding=config.get('default_encoding', 'gb18030'),
                codepage=config.get('codepage', 'gb18030'),
                international=config.get('international', 'FRANCE')
            )
            current_app.logger.debug('Command-capturing printer created')
            
            # Print exercise with real printer (captures commands)
            current_app.logger.debug('Printing exercise to capture commands...')
            state_manager = StateManager(storage)
            success = real_printer.print_exercise(
                exercise,
                daily=daily,
                city=city,
                course=course,
                storage=storage,
                state_manager=state_manager
            )
            
            if not success:
                current_app.logger.error('print_exercise returned False')
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de la génération des commandes'
                }), 500
            
            current_app.logger.debug(f'Captured {len(captured_commands)} ESC/POS commands')
            
            # Now replay commands in visual simulator
            current_app.logger.debug('Creating VisualSimulatorPrinter...')
            visual_printer = VisualSimulatorPrinter(
                device='/dev/null',
                width=config.get('width', 58),
                baudrate=9600,
                timeout=1,
                width_px=config.get('width_px', 384),
                default_encoding=config.get('default_encoding', 'gb18030'),
                codepage=config.get('codepage', 'gb18030'),
                international=config.get('international', 'FRANCE')
            )
            current_app.logger.debug('VisualSimulatorPrinter created successfully')
            
            # Réinitialiser explicitement avant de rejouer les commandes
            visual_printer._handle_reset()
            current_app.logger.debug('Visual simulator reset to blank state')
            
            # Replay all captured commands
            current_app.logger.debug(f'Replaying {len(captured_commands)} captured commands in visual simulator...')
            print_image_count = 0
            for i, (data, description) in enumerate(captured_commands):
                # Log PRINT_IMAGE commands
                if data.startswith(b"\x1D\x76\x30"):
                    print_image_count += 1
                    current_app.logger.debug(f'Replaying PRINT_IMAGE command #{print_image_count} ({len(data)} bytes)')
                visual_printer.raw(data, description)
            
            current_app.logger.debug(f'Replayed {print_image_count} PRINT_IMAGE commands')
            
            current_app.logger.debug('Commands replayed, getting preview image...')
            
            # Get preview image
            preview_img = visual_printer.get_preview_image()
            if not preview_img:
                current_app.logger.error('get_preview_image returned None')
                return jsonify({
                    'success': False,
                    'error': 'Impossible de générer l\'aperçu (image vide)'
                }), 500
            
            current_app.logger.debug(f'Preview image obtained: {preview_img.size}, mode={preview_img.mode}')
            
            # Save to temporary file
            import tempfile
            import os
            current_app.logger.debug('Creating temporary file...')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_path = temp_file.name
            temp_file.close()
            current_app.logger.debug(f'Temporary file created: {temp_path}')
            
            # Convert to RGB and save
            current_app.logger.debug('Converting image to RGB...')
            rgb_img = preview_img.convert("RGB")
            current_app.logger.debug('Saving image to file...')
            rgb_img.save(temp_path, "PNG")
            current_app.logger.debug('Image saved successfully')
            
            visual_printer.close()
            real_printer.close()
            current_app.logger.info('Visual preview generated successfully')
            
            # Return the image file
            return send_file(
                temp_path,
                mimetype='image/png',
                as_attachment=False,
                download_name=f'preview_{exercise.get("id", "exercise")}.png'
            )
            
        except ImportError as e:
            current_app.logger.error(f'ImportError: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': f'VisualSimulatorPrinter non disponible (PIL requis): {str(e)}'
            }), 500
        except Exception as e:
            current_app.logger.error(f'Error in VisualSimulatorPrinter section: {str(e)}', exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Erreur lors de la simulation: {str(e)}'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f'Error generating visual preview: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erreur générale: {str(e)}'
        }), 500

