"""Print routes for web interface."""

from flask import Blueprint, jsonify, request, current_app, render_template, send_file
from pathlib import Path
from src.web.app import storage
from src.printer import get_printer
from src.core.selector import select_exercise
from src.core.daily_selector import select_daily
from src.core.course_selector import select_course
from src.core.city_selector import select_city
from src.core.state_manager import StateManager

bp = Blueprint('print', __name__, url_prefix='/print')


@bp.route('/exercise', methods=['POST'])
def print_exercise():
    """Print a new exercise."""
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
            return jsonify({
                'success': False,
                'error': 'Aucun exercice disponible'
            }), 400
        
        # Select daily bonus
        daily = select_daily(storage)
        
        # Select course
        course = select_course(storage)
        
        # Select city for "ville du jour"
        city = select_city()
        
        # Get printer
        printer = get_printer()
        state_manager = StateManager(storage)
        
        # Print
        success = printer.print_exercise(
            exercise,
            daily=daily,
            city=city,
            course=course,
            storage=storage,
            state_manager=state_manager
        )
        
        if success:
            return jsonify({
                'success': True,
                'exercise_id': exercise.get('id'),
                'title': exercise.get('title')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'impression'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Error printing exercise: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/answers', methods=['POST'])
def print_answers():
    """Print answers for last exercise."""
    try:
        # Get state
        state = storage.get_state()
        exercise_id = state.get('last_exercise_id')
        
        if not exercise_id:
            return jsonify({
                'success': False,
                'error': 'Aucun exercice imprimé récemment'
            }), 400
        
        # Get printer
        printer = get_printer()
        state_manager = StateManager(storage)
        
        # Print answers
        success = printer.print_answers(
            exercise_id,
            storage=storage,
            state_manager=state_manager
        )
        
        if success:
            return jsonify({
                'success': True,
                'exercise_id': exercise_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'impression'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Error printing answers: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test', methods=['GET'])
def test_print_page():
    """Display test print page."""
    return render_template('test_print.html')


@bp.route('/test', methods=['POST'])
def test_print():
    """Test printing individual elements."""
    try:
        data = request.get_json() or {}
        test_type = data.get('type', 'text')
        
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        # Réinitialiser l'alignement
        printer.set_align("left")
        
        if test_type == 'separator':
            char = data.get('char', '-')
            double = data.get('double', False)
            printer.separator(char=char, double=double)
            printer.lf(2)
            
        elif test_type == 'text':
            text = data.get('text', 'Texte de test avec accents: à é è ç')
            printer.line(text)
            printer.lf(2)
            
        elif test_type == 'emoji':
            text = data.get('text', 'Emojis: 🎉 ✅ 🚀 🎯')
            printer.print_text_image(text=text, font_size=24, align="left")
            printer.lf(2)
            
        elif test_type == 'mixed':
            text = data.get('text', 'Texte normal avec emoji 🎉 et accents: à é è')
            printer.print_text_image(text=text, font_size=20, align="left")
            printer.lf(2)
            
        elif test_type == 'image':
            img_type = data.get('image_type', 'logo')
            if img_type == 'logo':
                logo_path = Path(__file__).parent.parent.parent / 'data' / 'logo_print.png'
                if logo_path.exists():
                    printer.set_align("center")
                    printer.print_image_file(str(logo_path))
                    printer.set_align("left")
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Logo non trouvé'
                    }), 404
            printer.lf(2)
            
        elif test_type == 'accent':
            texts = [
                "Accents français: à é è ê ë ï ô ù ç",
                "Majuscules: É È Ê Ë À Â Ä Ç Ù Û Ü Ô Ö Î Ï",
                "Mots: être médiévale événements allongé"
            ]
            for text in texts:
                printer.line(text)
            printer.lf(2)
            
        elif test_type == 'combination':
            printer.set_text_style(font="B", bold=True)
            printer.line("TEST COMBINÉ")
            printer.set_text_style()
            printer.separator(char="-", double=False)
            printer.line("Texte simple avec accents: à é è ç")
            printer.separator(char="=", double=True)
            printer.print_text_image(text="Texte avec emoji 🎉", font_size=20, align="left")
            printer.separator(char="-", double=False)
            printer.lf(2)
            
        else:
            return jsonify({
                'success': False,
                'error': f'Type de test inconnu: {test_type}'
            }), 400
        
        printer.cut(full=True)
        
        return jsonify({
            'success': True,
            'test_type': test_type
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in test print: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs')
def list_logs():
    """List recent print logs."""
    try:
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / 'logs'
        
        if not logs_dir.exists():
            return jsonify({
                'success': True,
                'logs': []
            })
        
        log_files = sorted(logs_dir.glob('printer_commands_*.log'), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
        
        logs = []
        for log_file in log_files:
            logs.append({
                'filename': log_file.name,
                'size': log_file.stat().st_size,
                'modified': log_file.stat().st_mtime
            })
        
        return jsonify({
            'success': True,
            'logs': logs
        })
        
    except Exception as e:
        current_app.logger.error(f'Error listing logs: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs/<filename>')
def view_log(filename):
    """View a specific log file."""
    try:
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / 'logs' / filename
        
        if not filename.startswith('printer_commands_') or not filename.endswith('.log'):
            return jsonify({
                'success': False,
                'error': 'Nom de fichier invalide'
            }), 400
        
        if not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Fichier non trouvé'
            }), 404
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'content': content
        })
        
    except Exception as e:
        current_app.logger.error(f'Error viewing log: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs/<filename>/download')
def download_log(filename):
    """Download a log file."""
    try:
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / 'logs' / filename
        
        if not filename.startswith('printer_commands_') or not filename.endswith('.log'):
            return jsonify({
                'success': False,
                'error': 'Nom de fichier invalide'
            }), 400
        
        if not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Fichier non trouvé'
            }), 404
        
        return send_file(str(log_file), as_attachment=True, download_name=filename)
        
    except Exception as e:
        current_app.logger.error(f'Error downloading log: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test', methods=['GET'])
def test_print_page():
    """Display test print page."""
    return render_template('test_print.html')


@bp.route('/test', methods=['POST'])
def test_print():
    """Test printing individual elements."""
    try:
        data = request.get_json() or {}
        test_type = data.get('type', 'text')
        
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        # Réinitialiser l'alignement
        printer.set_align("left")
        
        if test_type == 'separator':
            char = data.get('char', '-')
            double = data.get('double', False)
            printer.separator(char=char, double=double)
            printer.lf(2)
            
        elif test_type == 'text':
            text = data.get('text', 'Texte de test avec accents: à é è ç')
            printer.line(text)
            printer.lf(2)
            
        elif test_type == 'emoji':
            text = data.get('text', 'Emojis: 🎉 ✅ 🚀 🎯')
            printer.print_text_image(text=text, font_size=24, align="left")
            printer.lf(2)
            
        elif test_type == 'mixed':
            text = data.get('text', 'Texte normal avec emoji 🎉 et accents: à é è')
            # Pour l'instant, on utilise print_text_image pour les emojis
            printer.print_text_image(text=text, font_size=20, align="left")
            printer.lf(2)
            
        elif test_type == 'image':
            img_type = data.get('image_type', 'logo')
            if img_type == 'logo':
                logo_path = Path(__file__).parent.parent.parent / 'data' / 'logo_print.png'
                if logo_path.exists():
                    printer.set_align("center")
                    printer.print_image_file(str(logo_path))
                    printer.set_align("left")
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Logo non trouvé'
                    }), 404
            printer.lf(2)
            
        elif test_type == 'accent':
            texts = [
                "Accents français: à é è ê ë ï ô ù ç",
                "Majuscules: É È Ê Ë À Â Ä Ç Ù Û Ü Ô Ö Î Ï",
                "Mots: être médiévale événements allongé"
            ]
            for text in texts:
                printer.line(text)
            printer.lf(2)
            
        elif test_type == 'combination':
            # Test combiné
            printer.set_text_style(font="B", bold=True)
            printer.line("TEST COMBINÉ")
            printer.set_text_style()
            printer.separator(char="-", double=False)
            printer.line("Texte simple avec accents: à é è ç")
            printer.separator(char="=", double=True)
            printer.print_text_image(text="Texte avec emoji 🎉", font_size=20, align="left")
            printer.separator(char="-", double=False)
            printer.lf(2)
            
        else:
            return jsonify({
                'success': False,
                'error': f'Type de test inconnu: {test_type}'
            }), 400
        
        printer.cut(full=True)
        
        return jsonify({
            'success': True,
            'test_type': test_type
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in test print: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs')
def list_logs():
    """List recent print logs."""
    try:
        project_root = Path(__file__).parent.parent.parent
        logs_dir = project_root / 'logs'
        
        if not logs_dir.exists():
            return jsonify({
                'success': True,
                'logs': []
            })
        
        # Récupérer les fichiers de log récents (derniers 20)
        log_files = sorted(logs_dir.glob('printer_commands_*.log'), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
        
        logs = []
        for log_file in log_files:
            logs.append({
                'filename': log_file.name,
                'size': log_file.stat().st_size,
                'modified': log_file.stat().st_mtime
            })
        
        return jsonify({
            'success': True,
            'logs': logs
        })
        
    except Exception as e:
        current_app.logger.error(f'Error listing logs: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs/<filename>')
def view_log(filename):
    """View a specific log file."""
    try:
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / 'logs' / filename
        
        # Sécurité: vérifier que c'est bien un fichier de log
        if not filename.startswith('printer_commands_') or not filename.endswith('.log'):
            return jsonify({
                'success': False,
                'error': 'Nom de fichier invalide'
            }), 400
        
        if not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Fichier non trouvé'
            }), 404
        
        # Lire le contenu du log
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'content': content
        })
        
    except Exception as e:
        current_app.logger.error(f'Error viewing log: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs/<filename>/download')
def download_log(filename):
    """Download a log file."""
    try:
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / 'logs' / filename
        
        # Sécurité: vérifier que c'est bien un fichier de log
        if not filename.startswith('printer_commands_') or not filename.endswith('.log'):
            return jsonify({
                'success': False,
                'error': 'Nom de fichier invalide'
            }), 400
        
        if not log_file.exists():
            return jsonify({
                'success': False,
                'error': 'Fichier non trouvé'
            }), 404
        
        return send_file(str(log_file), as_attachment=True, download_name=filename)
        
    except Exception as e:
        current_app.logger.error(f'Error downloading log: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
