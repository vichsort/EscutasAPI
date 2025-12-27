import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from app.extensions import db, migrate, limiter

def create_app(config_name='default'):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "error": "Você está indo rápido demais!", 
            "description": f"Limite excedido: {e.description}"
        }), 429

    # Captura erro 500 (Internal Server Error) genérico
    @app.errorhandler(500)
    def internal_error(e):
        # Em produção, você logaria o erro real 'e' em um arquivo de log aqui
        # app.logger.error(f"Erro Crítico: {e}")
        return jsonify({
            "error": "Erro interno do servidor.",
            "message": "Nossa equipe já foi notificada. Tente novamente mais tarde."
        }), 500

    # Captura erro 404 (Not Found)
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso não encontrado"}), 404

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