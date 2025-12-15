"""Upload routes for photos and files."""

import os
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

bp = Blueprint('upload', __name__, url_prefix='/upload')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/surprise_photo', methods=['POST'])
def upload_surprise_photo():
    """Upload a surprise photo for daily items."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Extension non autorisée. Autorisées: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Get project root
        project_root = Path(__file__).parent.parent.parent.parent
        upload_dir = project_root / 'data' / 'surprise_photos'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        filepath = upload_dir / filename
        
        # If file exists, add a number suffix
        counter = 1
        original_filename = filename
        while filepath.exists():
            name, ext = original_filename.rsplit('.', 1)
            filename = f"{name}_{counter}.{ext}"
            filepath = upload_dir / filename
            counter += 1
        
        # Traiter l'image : redimensionner à 384px de large et convertir en noir et blanc
        if PIL_AVAILABLE:
            try:
                # Charger l'image
                img = Image.open(file.stream)
                
                # Convertir en RGB si nécessaire (pour les PNG avec transparence, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionner à 384px de large (proportionnellement)
                width, height = img.size
                if width > 384:
                    ratio = 384 / float(width)
                    new_height = int(height * ratio)
                    img = img.resize((384, new_height), Image.LANCZOS)
                
                # Convertir en niveaux de gris puis en noir et blanc (1-bit)
                img = img.convert('L')  # Niveaux de gris
                img = img.convert('1')  # Noir et blanc (1-bit)
                
                # Sauvegarder l'image traitée (toujours en PNG pour le 1-bit)
                filename_png = filename.rsplit('.', 1)[0] + '.png'
                filepath = upload_dir / filename_png
                
                # Si le fichier PNG existe déjà, ajouter un suffixe
                counter_png = 1
                original_filename_png = filename_png
                while filepath.exists():
                    name = original_filename_png.rsplit('.', 1)[0]
                    filename_png = f"{name}_{counter_png}.png"
                    filepath = upload_dir / filename_png
                    counter_png += 1
                
                img.save(str(filepath), 'PNG')
                filename = filename_png
            except Exception as e:
                current_app.logger.error(f'Error processing image: {str(e)}', exc_info=True)
                # Fallback: sauvegarder l'original si le traitement échoue
                file.stream.seek(0)  # Réinitialiser le stream
                file.save(str(filepath))
        else:
            # Si PIL n'est pas disponible, sauvegarder l'original
            file.save(str(filepath))
        
        # Si c'est une requête JSON (API)
        if request.is_json:
            return jsonify({
                'success': True,
                'filename': filename,
                'path': f"data/surprise_photos/{filename}"
            })
        
        # Sinon, rediriger vers la page de liste
        flash(f'Photo {filename} uploadée avec succès', 'success')
        return redirect(url_for('upload.list_surprise_photos'))
        
    except Exception as e:
        current_app.logger.error(f'Error uploading photo: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/surprise_photos', methods=['GET'])
def list_surprise_photos():
    """List all uploaded surprise photos."""
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        upload_dir = project_root / 'data' / 'surprise_photos'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        photos = []
        for filepath in upload_dir.iterdir():
            if filepath.is_file() and allowed_file(filepath.name):
                size = filepath.stat().st_size
                photos.append({
                    'filename': filepath.name,
                    'path': f"data/surprise_photos/{filepath.name}",
                    'size': size,
                    'size_mb': round(size / (1024 * 1024), 2)
                })
        
        # Si c'est une requête JSON (API)
        if request.args.get('format') == 'json' or request.is_json:
            return jsonify({
                'success': True,
                'photos': sorted(photos, key=lambda x: x['filename'])
            })
        
        # Sinon, afficher la page HTML
        return render_template('upload_photos.html', photos=sorted(photos, key=lambda x: x['filename']))
        
    except Exception as e:
        current_app.logger.error(f'Error listing photos: {str(e)}', exc_info=True)
        if request.args.get('format') == 'json' or request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('upload_photos.html', photos=[])


@bp.route('/surprise_photo/delete/<filename>', methods=['POST'])
def delete_surprise_photo(filename):
    """Delete a surprise photo."""
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        upload_dir = project_root / 'data' / 'surprise_photos'
        filepath = upload_dir / secure_filename(filename)
        
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            flash(f'Photo {filename} supprimée avec succès', 'success')
        else:
            flash(f'Photo {filename} non trouvée', 'error')
        
        return redirect(url_for('upload.list_surprise_photos'))
        
    except Exception as e:
        current_app.logger.error(f'Error deleting photo: {str(e)}', exc_info=True)
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('upload.list_surprise_photos'))

