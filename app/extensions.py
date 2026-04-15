from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()
jwt = JWTManager()

def register_extensions(app):
    """Inicializa todas as extensões do Flask."""
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    cache.init_app(app)
    jwt.init_app(app)