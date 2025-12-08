"""Flask application for Dutch-o-matic admin interface."""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, request, render_template_string
from src.storage import JSONStorage

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize storage
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
data_dir = os.path.join(project_root, 'data')
try:
    storage = JSONStorage(data_dir=data_dir)
except Exception as e:
    # Log to stderr since logging might not be set up yet
    import sys
    print(f'ERROR: Failed to initialize storage: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc()
    raise

# Setup logging
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Always add console handler first (for errors during startup)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
app.logger.addHandler(console_handler)

# Try to setup file logging
logs_dir = Path(project_root) / 'logs'
try:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / 'dutchomatic.log'
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.info(f'File logging initialized: {log_file}')
except Exception as e:
    app.logger.error(f'Failed to setup file logging: {e}', exc_info=True)
    app.logger.warning('Logging to console only')

# Configure Flask logger
app.logger.setLevel(logging.INFO)

# Also log to console in debug mode with more verbosity
if os.environ.get('FLASK_DEBUG', 'False').lower() == 'true':
    console_handler.setLevel(logging.DEBUG)

# Log requests
@app.before_request
def log_request_info():
    """Log request information."""
    app.logger.info(f'{request.method} {request.path} - IP: {request.remote_addr}')

@app.after_request
def log_response_info(response):
    """Log response information."""
    app.logger.info(f'{request.method} {request.path} - Status: {response.status_code}')
    return response

# Log errors
@app.errorhandler(500)
def log_internal_error(error):
    """Log internal server errors."""
    app.logger.error(f'Internal Server Error on {request.path}: {str(error)}', exc_info=True)
    error_template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Erreur serveur</title></head>
    <body>
        <h1>Erreur serveur interne</h1>
        <p>Une erreur s'est produite. Veuillez consulter les logs pour plus de détails.</p>
        <p><a href="/">Retour à l'accueil</a></p>
    </body>
    </html>
    '''
    return render_template_string(error_template), 500

@app.errorhandler(404)
def log_not_found(error):
    """Log 404 errors."""
    app.logger.warning(f'404 Not Found: {request.path}')
    error_template = '''
    <!DOCTYPE html>
    <html>
    <head><title>Page non trouvée</title></head>
    <body>
        <h1>404 - Page non trouvée</h1>
        <p><a href="/">Retour à l'accueil</a></p>
    </body>
    </html>
    '''
    return render_template_string(error_template), 404

# Register blueprints
from src.web.routes import dashboard, exercises, daily, settings, stats

app.register_blueprint(dashboard.bp)
app.register_blueprint(exercises.bp)
app.register_blueprint(daily.bp)
app.register_blueprint(settings.bp)
app.register_blueprint(stats.bp)


def create_app():
    """Application factory."""
    return app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
