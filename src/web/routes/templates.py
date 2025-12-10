"""Ticket template management routes."""

import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from src.core.ticket_templates import TicketTemplateManager

bp = Blueprint('templates', __name__, url_prefix='/templates')

template_manager = TicketTemplateManager()


@bp.route('/')
def list_templates():
    """List all ticket templates."""
    templates = template_manager.get_templates()
    return render_template('templates.html', templates=templates)


@bp.route('/<template_id>')
def view_template(template_id):
    """View a single template."""
    template = template_manager.get_template(template_id)
    if not template:
        flash('Template non trouvé', 'error')
        return redirect(url_for('templates.list_templates'))
    return render_template('template_detail.html', template=template)


@bp.route('/create', methods=['GET', 'POST'])
def create_template():
    """Create a new template."""
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                # Build data from form
                data = {
                    'id': request.form.get('id'),
                    'name': request.form.get('name'),
                    'type': request.form.get('type', 'exercise'),
                    'enabled': request.form.get('enabled') == 'on',
                    'header': {
                        'image': request.form.get('header_image') or None,
                        'custom_text': request.form.get('header_custom_text') or None
                    },
                    'content': {
                        'show_title': request.form.get('show_title') == 'on',
                        'show_niveau': request.form.get('show_niveau') == 'on',
                        'show_prompt': request.form.get('show_prompt') == 'on',
                        'max_items': int(request.form.get('max_items')) if request.form.get('max_items') else None,
                        'item_format': request.form.get('item_format', 'numbered')
                    },
                    'footer': {
                        'image': request.form.get('footer_image') or None,
                        'custom_text': request.form.get('footer_custom_text') or None
                    }
                }
            
            template_id = template_manager.add_template(data)
            
            if request.is_json:
                return jsonify({'success': True, 'id': template_id})
            flash('Template créé avec succès', 'success')
            return redirect(url_for('templates.view_template', template_id=template_id))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('template_form.html', template=None)


@bp.route('/<template_id>/edit', methods=['GET', 'POST'])
def edit_template(template_id):
    """Edit an existing template."""
    template = template_manager.get_template(template_id)
    if not template:
        flash('Template non trouvé', 'error')
        return redirect(url_for('templates.list_templates'))
    
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                # Build data from form
                data = {
                    'name': request.form.get('name'),
                    'type': request.form.get('type', 'exercise'),
                    'enabled': request.form.get('enabled') == 'on',
                    'header': {
                        'image': request.form.get('header_image') or None,
                        'custom_text': request.form.get('header_custom_text') or None
                    },
                    'content': {
                        'show_title': request.form.get('show_title') == 'on',
                        'show_niveau': request.form.get('show_niveau') == 'on',
                        'show_prompt': request.form.get('show_prompt') == 'on',
                        'max_items': int(request.form.get('max_items')) if request.form.get('max_items') else None,
                        'item_format': request.form.get('item_format', 'numbered')
                    },
                    'footer': {
                        'image': request.form.get('footer_image') or None,
                        'custom_text': request.form.get('footer_custom_text') or None
                    }
                }
            
            success = template_manager.update_template(template_id, data)
            
            if request.is_json:
                return jsonify({'success': success})
            if success:
                flash('Template modifié avec succès', 'success')
            else:
                flash('Erreur lors de la modification', 'error')
            return redirect(url_for('templates.view_template', template_id=template_id))
        except Exception as e:
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('template_form.html', template=template)


@bp.route('/<template_id>/delete', methods=['POST'])
def delete_template(template_id):
    """Delete a template."""
    try:
        success = template_manager.delete_template(template_id)
        if request.is_json:
            return jsonify({'success': success})
        if success:
            flash('Template supprimé avec succès', 'success')
        else:
            flash('Template non trouvé', 'error')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('templates.list_templates'))


@bp.route('/reorder', methods=['POST'])
def reorder_templates():
    """Reorder templates."""
    try:
        if request.is_json:
            data = request.get_json()
            template_ids = data.get('template_ids', [])
        else:
            template_ids = request.form.getlist('template_ids')
        
        success = template_manager.reorder_templates(template_ids)
        
        if request.is_json:
            return jsonify({'success': success})
        if success:
            flash('Ordre des templates mis à jour', 'success')
        else:
            flash('Erreur lors de la réorganisation', 'error')
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('templates.list_templates'))

