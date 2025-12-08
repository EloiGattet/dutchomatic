"""Daily management routes."""

import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from src.web.app import storage
from src.utils.validators import validate_daily

bp = Blueprint('daily', __name__, url_prefix='/daily')


@bp.route('/')
def list_daily():
    """List all daily items with filters."""
    kind = request.args.get('kind')
    daily_items = storage.get_all_daily(kind=kind)
    return render_template('daily.html', daily_items=daily_items, filter_kind=kind)


@bp.route('/create', methods=['GET', 'POST'])
def create_daily():
    """Create a new daily item."""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            daily_id = storage.add_daily(data)
            if request.is_json:
                return jsonify({'success': True, 'id': daily_id})
            flash('Élément daily créé avec succès', 'success')
            return redirect(url_for('daily.list_daily'))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('daily_form.html', daily=None)


@bp.route('/<daily_id>/edit', methods=['GET', 'POST'])
def edit_daily(daily_id):
    """Edit an existing daily item."""
    daily_item = storage.get_daily(daily_id)
    if not daily_item:
        flash('Élément daily non trouvé', 'error')
        return redirect(url_for('daily.list_daily'))
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            storage.update_daily(daily_id, data)
            if request.is_json:
                return jsonify({'success': True})
            flash('Élément daily modifié avec succès', 'success')
            return redirect(url_for('daily.list_daily'))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('daily_form.html', daily=daily_item)


@bp.route('/<daily_id>/delete', methods=['POST'])
def delete_daily(daily_id):
    """Delete a daily item."""
    try:
        storage.delete_daily(daily_id)
        if request.is_json:
            return jsonify({'success': True})
        flash('Élément daily supprimé avec succès', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('daily.list_daily'))


@bp.route('/export')
def export_daily():
    """Export all daily items as JSON."""
    daily_items = storage.get_all_daily()
    return jsonify(daily_items), 200, {'Content-Type': 'application/json; charset=utf-8'}


@bp.route('/import', methods=['POST'])
def import_daily():
    """Import daily items from JSON."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = json.loads(request.form.get('json_data', '[]'))
        
        imported = 0
        errors = []
        for item in data:
            try:
                storage.add_daily(item)
                imported += 1
            except Exception as e:
                errors.append(f"{item.get('id', 'unknown')}: {str(e)}")
        
        if request.is_json:
            return jsonify({'success': True, 'imported': imported, 'errors': errors})
        flash(f'{imported} élément(s) importé(s)', 'success')
        if errors:
            flash(f'Erreurs: {", ".join(errors)}', 'warning')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('daily.list_daily'))
