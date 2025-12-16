"""Print routes for web interface."""

from flask import Blueprint, jsonify, request, current_app, render_template, send_file
from pathlib import Path
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
        storage = current_app.extensions['storage']
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
        
        # Réinitialiser tous les paramètres avant chaque test
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        else:
            # Fallback si la méthode n'existe pas
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
                logo_path = Path(__file__).parent.parent.parent.parent / 'data' / 'logo_print.png'
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
            # Tester uniquement les accents supportés par GB18030: à é è ê ù
            texts = [
                "Accents supportés GB18030: à é è ê ù",
                "Mots: être événements allongé",
                "Test caractères: € — …"
            ]
            for text in texts:
                printer.line(text)
            printer.lf(2)
            
        elif test_type == 'combination':
            printer.set_text_style(font="B", bold=True)
            printer.line("TEST COMBINÉ")
            printer.set_text_style()
            # Utiliser chars_per_line automatiquement (s'adapte à la font active)
            printer.separator(char="—", double=False)
            printer.line("Texte simple avec accents: à é è ê ù")
            printer.separator(char="—", double=True)
            printer.print_text_image(text="Texte avec emoji 🎉", font_size=20, align="left")
            printer.separator(char="—", double=False)
            printer.lf(2)
            
        else:
            return jsonify({
                'success': False,
                'error': f'Type de test inconnu: {test_type}'
            }), 400
        
        printer.cut(full=True, close_after=True)
        
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


@bp.route('/test/exercises')
def list_exercises():
    """List all available exercises for testing."""
    try:
        storage = current_app.extensions['storage']
        exercises = storage.get_all_exercises()
        
        # Format for frontend
        exercises_list = []
        for ex in exercises:
            exercises_list.append({
                'id': ex.get('id'),
                'title': ex.get('title'),
                'niveau': ex.get('niveau'),
                'type': ex.get('type')
            })
        
        return jsonify({
            'success': True,
            'exercises': exercises_list
        })
    except Exception as e:
        current_app.logger.error(f'Error listing exercises: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/exercise/<exercise_id>', methods=['POST'])
def test_exercise(exercise_id):
    """Test printing a specific exercise."""
    try:
        storage = current_app.extensions['storage']
        exercise = storage.get_exercise(exercise_id)
        
        if not exercise:
            return jsonify({
                'success': False,
                'error': f'Exercice {exercise_id} non trouvé'
            }), 404
        
        # Select daily bonus, city, course for testing
        daily = select_daily(storage)
        city = select_city()
        course = select_course(storage)
        
        # Get printer
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        # Réinitialiser les paramètres
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Print exercise
        state_manager = StateManager(storage)
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
                'exercise_id': exercise_id,
                'title': exercise.get('title')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'impression'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Error testing exercise: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/header', methods=['POST'])
def test_header():
    """Test header section (logo, custom text)."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Test logo
        logo_path = Path(__file__).parent.parent.parent.parent / 'data' / 'logo_print.png'
        if logo_path.exists():
            printer.set_align("center")
            printer.print_image_file(str(logo_path))
            printer.set_align("left")
        
        # Test date et message
        from datetime import datetime
        current_date = datetime.now().strftime('%d/%m/%Y')
        printer.centered_text(current_date)
        printer.centered_text("Goed gedaan!")
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error in test header: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/content', methods=['POST'])
def test_content():
    """Test content section (title, prompt, items)."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Test séparateur (em-dash compatible GB18030, largeur selon font active)
        printer.separator(char="—", double=False)
        
        # Test titre
        printer.centered_text("EXERCICE — Test de contenu (A1)")
        
        # Test prompt
        printer.line("Traduisez les phrases suivantes en français:")
        printer.lf(1)
        
        # Test items
        test_items = [
            "1. Ik ga naar de winkel",
            "   Je vais au magasin",
            "2. Hoe gaat het?",
            "   Comment ça va?",
            "3. Goedemorgen!",
            "   Bonjour!"
        ]
        for item in test_items:
            printer.line(item)
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error in test content: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/bonus', methods=['POST'])
def test_bonus():
    """Test bonus section (phrase du jour, recette, photo, défi)."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Test phrase du jour (em-dash compatible GB18030)
        printer.separator(char="—", double=False)
        printer.centered_text("🎁 PHRASE DU JOUR")
        printer.line("Goedemorgen → Bonjour")
        printer.lf(1)
        
        # Test recette (em-dash compatible GB18030)
        printer.separator(char="—", double=False)
        printer.centered_text("🍳 RECETTE")
        printer.line("Ingrédients: farine, œufs, lait")
        printer.line("Mélanger et cuire 20 minutes")
        printer.lf(1)
        
        # Test photo surprise
        printer.centered_text("📸 Photo surprise")
        printer.lf(1)
        
        # Test défi (em-dash compatible GB18030)
        printer.separator(char="—", double=False)
        printer.centered_text("💪 DÉFI DU JOUR")
        printer.line("Apprenez 5 nouveaux mots aujourd'hui!")
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error in test bonus: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/city', methods=['POST'])
def test_city():
    """Test city section (ville du jour, météo, carte)."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Test ville du jour (em-dash compatible GB18030)
        printer.separator(char="—", double=False)
        printer.centered_text("🏙️  VILLE DU JOUR")
        printer.line("Amsterdam")
        printer.line("Capitale des Pays-Bas")
        printer.lf(1)
        
        # Test météo
        printer.line("☀️ 20°C - Ensoleillé")
        printer.lf(1)
        
        # Test carte (juste un message pour l'instant)
        printer.line("📍 Carte de la ville")
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error in test city: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/surprise-photos')
def list_surprise_photos():
    """List all available surprise photos for testing."""
    try:
        # Chemin: src/web/routes/print.py -> src/web/routes -> src/web -> src -> racine
        project_root = Path(__file__).parent.parent.parent.parent
        photos_dir = project_root / 'data' / 'surprise_photos'
        
        if not photos_dir.exists():
            return jsonify({
                'success': True,
                'photos': []
            })
        
        # Liste tous les fichiers image
        photo_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']:
            photo_files.extend(photos_dir.glob(ext))
        
        photos_list = []
        for photo_file in sorted(photo_files):
            photos_list.append({
                'filename': photo_file.name,
                'path': str(photo_file.relative_to(project_root))
            })
        
        return jsonify({
            'success': True,
            'photos': photos_list
        })
    except Exception as e:
        current_app.logger.error(f'Error listing surprise photos: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/surprise-photo/<filename>', methods=['POST'])
def test_surprise_photo(filename):
    """Test printing a specific surprise photo."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Chemin: src/web/routes/print.py -> src/web/routes -> src/web -> src -> racine
        project_root = Path(__file__).parent.parent.parent.parent
        photo_path = project_root / 'data' / 'surprise_photos' / filename
        
        # Sécurité : vérifier que le fichier est dans le bon répertoire
        if not photo_path.exists() or not str(photo_path).startswith(str(project_root / 'data' / 'surprise_photos')):
            return jsonify({
                'success': False,
                'error': 'Photo non trouvée ou chemin invalide'
            }), 404
        
        # Test de la photo
        printer.centered_text("📸 Photo surprise")
        printer.lf(1)
        printer.set_align("center")
        success = printer.print_image_file(str(photo_path))
        printer.set_align("left")
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'impression de la photo'
            }), 500
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({
            'success': True,
            'filename': filename
        })
    except Exception as e:
        current_app.logger.error(f'Error testing surprise photo: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/footer', methods=['POST'])
def test_footer():
    """Test footer section (encouragement, compteur)."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Test message d'encouragement (em-dash compatible GB18030)
        printer.separator(char="—", double=False)
        printer.centered_text("💪 Continuez comme ça!")
        printer.lf(1)
        
        # Test compteur
        printer.centered_text("Ticket #42")
        printer.centered_text("XP: 150")
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error in test footer: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test/center', methods=['POST'])
def test_center():
    """Test centrage de texte."""
    try:
        printer = get_printer()
        if not hasattr(printer, '_ser') or not printer._ser:
            return jsonify({
                'success': False,
                'error': 'Imprimante non initialisée'
            }), 500
        
        if hasattr(printer, 'reset_printer_settings'):
            printer.reset_printer_settings()
        
        # Test centrage avec différentes longueurs de texte
        printer.centered_text("Texte court")
        printer.centered_text("Texte un peu plus long")
        printer.centered_text("Texte très long qui devrait être centré correctement")
        printer.lf(1)
        
        # Test avec accents
        printer.centered_text("À é è ç")
        printer.centered_text("Goed gedaan!")
        printer.lf(1)
        
        # Test avec alignement manuel
        printer.set_align("center")
        printer.line("Alignement center")
        printer.set_align("left")
        printer.line("Alignement left")
        printer.set_align("right")
        printer.line("Alignement right")
        printer.set_align("left")
        
        printer.lf(2)
        printer.cut(full=True, close_after=True)
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'Error in test center: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/logs')
def list_logs():
    """List recent print logs."""
    try:
        project_root = Path(__file__).parent.parent.parent.parent
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
        project_root = Path(__file__).parent.parent.parent.parent
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
        project_root = Path(__file__).parent.parent.parent.parent
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
