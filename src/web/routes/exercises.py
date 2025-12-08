"""Exercise management routes."""

import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from src.web.app import storage
from src.utils.validators import validate_exercise

bp = Blueprint('exercises', __name__, url_prefix='/exercices')


@bp.route('/')
def list_exercises():
    """List all exercises with filters."""
    niveau = request.args.get('niveau')
    type_filter = request.args.get('type')
    tag = request.args.get('tag')
    
    filters = {}
    if niveau:
        filters['niveau'] = niveau
    if type_filter:
        filters['type'] = type_filter
    if tag:
        filters['tags'] = tag
    
    exercises = storage.get_all_exercises(filters)
    return render_template('exercises.html', exercises=exercises, filters=filters)


@bp.route('/<exercise_id>')
def view_exercise(exercise_id):
    """View a single exercise."""
    try:
        current_app.logger.info(f'Viewing exercise: {exercise_id}')
        exercise = storage.get_exercise(exercise_id)
        if not exercise:
            current_app.logger.warning(f'Exercise not found: {exercise_id}')
            flash('Exercice non trouvé', 'error')
            return redirect(url_for('exercises.list_exercises'))
        return render_template('exercise_detail.html', exercise=exercise)
    except Exception as e:
        current_app.logger.error(f'Error viewing exercise {exercise_id}: {str(e)}', exc_info=True)
        flash(f'Erreur lors de l\'affichage de l\'exercice: {str(e)}', 'error')
        return redirect(url_for('exercises.list_exercises'))


@bp.route('/create', methods=['GET', 'POST'])
def create_exercise():
    """Create a new exercise."""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            if 'items' in data and isinstance(data['items'], str):
                data['items'] = json.loads(data['items'])
            if 'tags' in data and isinstance(data['tags'], str):
                data['tags'] = json.loads(data['tags']) if data['tags'] else []
            
            exercise_id = storage.add_exercise(data)
            if request.is_json:
                return jsonify({'success': True, 'id': exercise_id})
            flash('Exercice créé avec succès', 'success')
            return redirect(url_for('exercises.view_exercise', exercise_id=exercise_id))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
            return redirect(url_for('exercises.list_exercises'))
    
    return render_template('exercise_form.html', exercise=None)


@bp.route('/<exercise_id>/edit', methods=['GET', 'POST'])
def edit_exercise(exercise_id):
    """Edit an existing exercise."""
    try:
        current_app.logger.info(f'Editing exercise: {exercise_id}')
        exercise = storage.get_exercise(exercise_id)
        if not exercise:
            current_app.logger.warning(f'Exercise not found for edit: {exercise_id}')
            flash('Exercice non trouvé', 'error')
            return redirect(url_for('exercises.list_exercises'))
        
        if request.method == 'POST':
            try:
                data = request.get_json() if request.is_json else request.form.to_dict()
                if 'items' in data and isinstance(data['items'], str):
                    data['items'] = json.loads(data['items'])
                if 'tags' in data and isinstance(data['tags'], str):
                    data['tags'] = json.loads(data['tags']) if data['tags'] else []
                
                storage.update_exercise(exercise_id, data)
                current_app.logger.info(f'Exercise updated: {exercise_id}')
                if request.is_json:
                    return jsonify({'success': True})
                flash('Exercice modifié avec succès', 'success')
                return redirect(url_for('exercises.view_exercise', exercise_id=exercise_id))
            except Exception as e:
                current_app.logger.error(f'Error updating exercise {exercise_id}: {str(e)}', exc_info=True)
                if request.is_json:
                    return jsonify({'success': False, 'error': str(e)}), 400
                flash(f'Erreur: {str(e)}', 'error')
        
        return render_template('exercise_form.html', exercise=exercise)
    except Exception as e:
        current_app.logger.error(f'Error displaying edit form for {exercise_id}: {str(e)}', exc_info=True)
        flash(f'Erreur lors de l\'affichage du formulaire: {str(e)}', 'error')
        return redirect(url_for('exercises.list_exercises'))


@bp.route('/<exercise_id>/delete', methods=['POST'])
def delete_exercise(exercise_id):
    """Delete an exercise."""
    try:
        storage.delete_exercise(exercise_id)
        if request.is_json:
            return jsonify({'success': True})
        flash('Exercice supprimé avec succès', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('exercises.list_exercises'))


@bp.route('/export')
def export_exercises():
    """Export all exercises as JSON."""
    exercises = storage.get_all_exercises()
    return jsonify(exercises), 200, {'Content-Type': 'application/json; charset=utf-8'}


@bp.route('/import', methods=['POST'])
def import_exercises():
    """Import exercises from JSON."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = json.loads(request.form.get('json_data', '[]'))
        
        imported = 0
        errors = []
        for ex in data:
            try:
                storage.add_exercise(ex)
                imported += 1
            except Exception as e:
                errors.append(f"{ex.get('id', 'unknown')}: {str(e)}")
        
        if request.is_json:
            return jsonify({'success': True, 'imported': imported, 'errors': errors})
        flash(f'{imported} exercice(s) importé(s)', 'success')
        if errors:
            flash(f'Erreurs: {", ".join(errors)}', 'warning')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('exercises.list_exercises'))
