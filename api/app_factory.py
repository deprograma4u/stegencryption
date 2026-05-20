
import os
from flask import Flask, render_template
from flask_cors import CORS

from api.routes.stego_routes import stego_bp
from api.routes.key_routes import key_bp
from config.settings import settings

# from ..routes.stego_routes import stego_bp
# from ..routes.key_routes import key_bp
# from ...config.settings import settings


# Creating the flask api entry
def create_app(config_name='development'):
    
    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    
    # Configure app
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_CONTENT_LENGTH
    app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER
    
    # Ensuring upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Enabling CORS for all routes
    CORS(app)
    
    # Registering blueprints
    app.register_blueprint(stego_bp)
    app.register_blueprint(key_bp)
    
    # health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {
            'status': 'healthy',
            'version': '1.0.0',
            'service': 'secure-steganography-api'
        }
    
    # root endpoint
    @app.route('/')
    def index():
        # return {
        #     'message': 'Secure Steganography API',
        #     'version': '1.0.0',
        #     'endpoints': {
        #         'steganography': '/api/stego',
        #         'keys': '/api/keys',
        #         'health': '/api/health'
        #     }
        # }

        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        return {
            'success': False,
            'message': 'File too large',
            'error_code': 'FILE_TOO_LARGE'
        }, 413
    
    @app.errorhandler(404)
    def not_found(e):
        return {
            'success': False,
            'message': 'Endpoint not found',
            'error_code': 'NOT_FOUND'
        }, 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return {
            'success': False,
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }, 500
    
    return app
