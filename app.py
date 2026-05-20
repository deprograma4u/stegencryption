
import os
from api.app_factory import create_app
from config.settings import settings

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=settings.DEBUG
    )