from .auth import auth_bp
from .albums import albums_bp
from .reviews import reviews_bp
from .me import me_bp
from .users import users_bp
from .blog import blog_bp

def register_blueprints(app):
    """Registra todos os blueprints da aplicação."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(albums_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(blog_bp)