"""Instagram accounts management routes."""

import json
import os
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for

bp = Blueprint('instagram', __name__, url_prefix='/instagram')


def get_instagram_file():
    """Get path to instagram accounts file."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(project_root, 'data', 'instagram_accounts.json')


def load_instagram_accounts():
    """Load Instagram accounts from file."""
    instagram_file = get_instagram_file()
    default_data = {
        'categories': []
    }
    
    if os.path.exists(instagram_file):
        try:
            with open(instagram_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_data
    
    return default_data


def save_instagram_accounts(data):
    """Save Instagram accounts to file."""
    instagram_file = get_instagram_file()
    os.makedirs(os.path.dirname(instagram_file), exist_ok=True)
    with open(instagram_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@bp.route('/')
def list_accounts():
    """List all Instagram accounts by category."""
    data = load_instagram_accounts()
    return render_template('instagram.html', categories=data.get('categories', []))


@bp.route('/update', methods=['POST'])
def update_accounts():
    """Update Instagram accounts."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            # Parse form data
            data = {'categories': []}
            # This is a simplified version - in production, you'd parse the form more carefully
            # For now, we'll use JSON input
            json_data = request.form.get('json_data', '')
            if json_data:
                data = json.loads(json_data)
        
        save_instagram_accounts(data)
        
        if request.is_json:
            return jsonify({'success': True})
        flash('Comptes Instagram mis à jour avec succès', 'success')
        return redirect(url_for('instagram.list_accounts'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('instagram.list_accounts'))

