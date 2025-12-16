"""Settings management routes."""

import json
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app

bp = Blueprint('settings', __name__, url_prefix='/settings')


def get_settings_file():
    """Get path to settings file."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(project_root, 'config', 'settings.json')


def load_settings():
    """Load settings from file."""
    settings_file = get_settings_file()
    default_settings = {
        'draw_policy': 'strict',
        'draw_mix_percent': 70,
        'level_thresholds': {
            'A1': 0,
            'A2': 100,
            'B1': 250,
            'B2': 500,
            'C1': 1000,
            'C2': 2000
        },
        'ai_enabled': False,
        'printer': {
            'type': 'simulator',
            'device': '/dev/usb/lp0',
            'width': 58
        }
    }
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                default_settings.update(user_settings)
        except:
            pass
    
    return default_settings


def save_settings(settings):
    """Save settings to file."""
    settings_file = get_settings_file()
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


@bp.route('/', methods=['GET', 'POST'])
def index():
    """Settings page."""
    if request.method == 'POST':
        try:
            settings = load_settings()
            
            # Update draw policy
            settings['draw_policy'] = request.form.get('draw_policy', 'strict')
            settings['draw_mix_percent'] = int(request.form.get('draw_mix_percent', 70))
            
            # Update level thresholds
            for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
                threshold = request.form.get(f'threshold_{level}')
                if threshold:
                    settings['level_thresholds'][level] = int(threshold)
            
            # Update AI
            settings['ai_enabled'] = request.form.get('ai_enabled') == 'on'
            
            # Update printer
            settings['printer']['type'] = request.form.get('printer_type', 'simulator')
            settings['printer']['device'] = request.form.get('printer_device', '/dev/usb/lp0')
            settings['printer']['width'] = int(request.form.get('printer_width', 58))
            
            save_settings(settings)
            
            # Update state: trip_date and encouragement_messages
            storage = current_app.extensions['storage']
            state = storage.get_state()
            trip_date = request.form.get('trip_date', '').strip()
            if trip_date:
                state['trip_date'] = trip_date
            else:
                state['trip_date'] = None
            
            # Messages d'encouragement (un par ligne)
            encouragement_text = request.form.get('encouragement_messages', '').strip()
            if encouragement_text:
                messages = [m.strip() for m in encouragement_text.split('\n') if m.strip()]
                if messages:
                    state['encouragement_messages'] = messages
            
            storage.update_state('trip_date', state['trip_date'])
            storage.update_state('encouragement_messages', state['encouragement_messages'])
            
            flash('Paramètres sauvegardés avec succès', 'success')
            return redirect(url_for('settings.index'))
        except Exception as e:
            flash(f'Erreur: {str(e)}', 'error')
    
    settings = load_settings()
    storage = current_app.extensions['storage']
    state = storage.get_state()
    return render_template('settings.html', settings=settings, state=state)
