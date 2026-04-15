import os
from flask import Flask
from flask_cors import CORS
from config import config
from app.extensions import register_extensions
from app.errors import register_error_handlers
from app.api import register_blueprints

def create_app(config_name='default'):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    register_extensions(app)
    register_error_handlers(app)

    from app import models

    register_blueprints(app)
    
    return app