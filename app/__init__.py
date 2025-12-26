from flask import Flask
from flask_cors import CORS
from config import config
from app.extensions import db, migrate

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Extensions

    # Import models to register them with SQLAlchemy
    from app.models.user import User
    from app.models.review import AlbumReview, TrackReview

    # Register Blueprints
    from app.api.auth import auth_bp
    from app.api.albums import albums_bp
    from app.api.reviews import reviews_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(albums_bp)
    app.register_blueprint(reviews_bp)
    
    return app