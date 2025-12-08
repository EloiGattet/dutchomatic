"""Statistics routes."""

from collections import defaultdict
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from src.web.app import storage

bp = Blueprint('stats', __name__, url_prefix='/stats')


@bp.route('/')
def index():
    """Statistics page."""
    exercises = storage.get_all_exercises()
    state = storage.get_state()
    history = state.get('history', [])
    
    # Distribution par type
    type_dist = defaultdict(int)
    for ex in exercises:
        type_dist[ex.get('type', 'unknown')] += 1
    
    # Distribution par niveau
    niveau_dist = defaultdict(int)
    for ex in exercises:
        niveau_dist[ex.get('niveau', 'unknown')] += 1
    
    # Tickets par jour (7 derniers jours)
    tickets_per_day = defaultdict(int)
    answers_per_day = defaultdict(int)
    today = datetime.now().date()
    
    for entry in history:
        try:
            printed_at = datetime.fromisoformat(entry.get('printed_at', '').replace('Z', '+00:00'))
            day = printed_at.date()
            if (today - day).days <= 7:
                tickets_per_day[day.isoformat()] += 1
                if entry.get('with_answers'):
                    answers_per_day[day.isoformat()] += 1
        except:
            pass
    
    # Taux de réponses imprimées
    total_prints = len(history)
    total_with_answers = sum(1 for e in history if e.get('with_answers'))
    answer_rate = (total_with_answers / total_prints * 100) if total_prints > 0 else 0
    
    stats_data = {
        'type_distribution': dict(type_dist),
        'niveau_distribution': dict(niveau_dist),
        'tickets_per_day': dict(tickets_per_day),
        'answers_per_day': dict(answers_per_day),
        'answer_rate': round(answer_rate, 1),
        'total_exercises': len(exercises),
        'total_prints': total_prints
    }
    
    return render_template('stats.html', **stats_data)


@bp.route('/api/data')
def api_data():
    """API endpoint for stats data."""
    exercises = storage.get_all_exercises()
    state = storage.get_state()
    history = state.get('history', [])
    
    type_dist = defaultdict(int)
    niveau_dist = defaultdict(int)
    
    for ex in exercises:
        type_dist[ex.get('type', 'unknown')] += 1
        niveau_dist[ex.get('niveau', 'unknown')] += 1
    
    return jsonify({
        'type_distribution': dict(type_dist),
        'niveau_distribution': dict(niveau_dist)
    })
