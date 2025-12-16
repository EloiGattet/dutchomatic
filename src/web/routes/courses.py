"""Course management routes."""

import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app

bp = Blueprint('courses', __name__, url_prefix='/courses')


@bp.route('/')
def list_courses():
    """List all courses with filters."""
    storage = current_app.extensions['storage']
    course_type = request.args.get('type')
    courses = storage.get_all_courses(course_type=course_type)
    return render_template('courses.html', courses=courses, filter_type=course_type)


@bp.route('/<course_id>')
def view_course(course_id):
    """View a single course."""
    storage = current_app.extensions['storage']
    course = storage.get_course(course_id)
    if not course:
        flash('Cours non trouvé', 'error')
        return redirect(url_for('courses.list_courses'))
    return render_template('course_detail.html', course=course)


@bp.route('/create', methods=['GET', 'POST'])
def create_course():
    """Create a new course."""
    if request.method == 'POST':
        try:
            storage = current_app.extensions['storage']
            data = request.get_json() if request.is_json else request.form.to_dict()
            # Parser examples si c'est une string JSON
            if 'examples' in data and isinstance(data['examples'], str) and data['examples'].strip():
                try:
                    data['examples'] = json.loads(data['examples'])
                except:
                    data['examples'] = []
            course_id = storage.add_course(data)
            if request.is_json:
                return jsonify({'success': True, 'id': course_id})
            flash('Cours créé avec succès', 'success')
            return redirect(url_for('courses.view_course', course_id=course_id))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('course_form.html', course=None)


@bp.route('/<course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    """Edit an existing course."""
    storage = current_app.extensions['storage']
    course = storage.get_course(course_id)
    if not course:
        flash('Cours non trouvé', 'error')
        return redirect(url_for('courses.list_courses'))
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            # Parser examples si c'est une string JSON
            if 'examples' in data and isinstance(data['examples'], str) and data['examples'].strip():
                try:
                    data['examples'] = json.loads(data['examples'])
                except:
                    data['examples'] = []
            storage = current_app.extensions['storage']
            storage.update_course(course_id, data)
            if request.is_json:
                return jsonify({'success': True})
            flash('Cours modifié avec succès', 'success')
            return redirect(url_for('courses.view_course', course_id=course_id))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('course_form.html', course=course)


@bp.route('/<course_id>/delete', methods=['POST'])
def delete_course(course_id):
    """Delete a course."""
    try:
        storage = current_app.extensions['storage']
        storage.delete_course(course_id)
        if request.is_json:
            return jsonify({'success': True})
        flash('Cours supprimé avec succès', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('courses.list_courses'))


@bp.route('/export')
def export_courses():
    """Export all courses as JSON."""
    storage = current_app.extensions['storage']
    courses = storage.get_all_courses()
    return jsonify(courses), 200, {'Content-Type': 'application/json; charset=utf-8'}


@bp.route('/import', methods=['POST'])
def import_courses():
    """Import courses from JSON."""
    try:
        storage = current_app.extensions['storage']
        if request.is_json:
            data = request.get_json()
        else:
            data = json.loads(request.form.get('json_data', '[]'))
        
        imported = 0
        errors = []
        for course in data:
            try:
                storage.add_course(course)
                imported += 1
            except Exception as e:
                errors.append(f"{course.get('id', 'unknown')}: {str(e)}")
        
        if request.is_json:
            return jsonify({'success': True, 'imported': imported, 'errors': errors})
        flash(f'{imported} cours importé(s)', 'success')
        if errors:
            flash(f'Erreurs: {", ".join(errors)}', 'warning')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('courses.list_courses'))

