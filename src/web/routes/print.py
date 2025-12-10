"""Print routes for web interface."""

from flask import Blueprint, jsonify, request, current_app
from src.web.app import storage
from src.printer import get_printer
from src.core.selector import select_exercise
from src.core.daily_selector import select_daily
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
        
        # Get printer
        printer = get_printer()
        state_manager = StateManager(storage)
        
        # Print
        success = printer.print_exercise(
            exercise,
            daily=daily,
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

