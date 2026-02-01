import os
from flask import Flask, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from config import config
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate, limiter, cache
from app.utils.response_util import APIError, handle_exception

def create_app(config_name='default'):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Extensões
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    cache.init_app(app)
    jwt = JWTManager(app)

    app.register_error_handler(APIError, handle_exception)

    # Erros de validação do Pydantic
    @app.errorhandler(ValidationError)
    def handle_pydantic_error(e):
        return jsonify({
            "status": "error",
            "message": "Erro de validação nos dados enviados.",
            "errors": e.errors()
        }), 400

    # Rate Limit (429)
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "status": "error",
            "message": "Você está indo rápido demais!", 
            "description": e.description
        }), 429

    # Rota não encontrada (404)
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Recurso não encontrado"}), 404

    # Captura 500 e Exceções Genéricas não tratadas
    app.register_error_handler(Exception, handle_exception)

    # Modelos pra leitura do SQLAlchemy
    from app.models.user import User
    from app.models.review import AlbumReview, TrackReview

    # Blueprints
    from app.api.auth import auth_bp
    from app.api.albums import albums_bp
    from app.api.reviews import reviews_bp
    from app.api.spotify_integration import spotify_bp
    from app.api.users import users_bp
    from app.api.blog import blog_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(albums_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(blog_bp)
    
    return app