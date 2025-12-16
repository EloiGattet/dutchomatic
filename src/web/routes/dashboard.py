"""Dashboard routes."""

from flask import Blueprint, render_template, current_app

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    """Dashboard home page."""
    storage = current_app.extensions['storage']
    state = storage.get_state()
    exercises = storage.get_all_exercises()
    daily_items = storage.get_all_daily()
    
    # Get last 10 history entries
    history = state.get('history', [])[-10:]
    history.reverse()
    
    # Get last exercise details if exists
    last_exercise = None
    if state.get('last_exercise_id'):
        last_exercise = storage.get_exercise(state['last_exercise_id'])
    
    stats_data = {
        'total_exercises': len(exercises),
        'total_daily': len(daily_items),
        'niveau_actuel': state.get('niveau_actuel', 'A1'),
        'xp': state.get('xp', 0),
        'compteur_total': state.get('compteur_total', 0),
        'last_exercise': last_exercise,
        'recent_history': history
    }
    
    return render_template('dashboard.html', **stats_data)
