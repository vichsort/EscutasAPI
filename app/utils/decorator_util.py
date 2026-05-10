from app.extensions import db
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User
from app.exceptions import ResourceNotFoundError, AuthenticationError

def require_auth(f):
    """
    Decorator para proteger rotas.
    Verifica se o usuário tem token atualizado para seguir
    para as rotas protegidas.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            current_user = db.session.get(User, user_id)
            
            if not current_user:
                raise ResourceNotFoundError("Usuário não encontrado.", 401)
                
        except Exception:
            raise AuthenticationError("Token inválido ou expirado.", 401)

        return f(current_user, *args, **kwargs)
        
    return decorated

def ensure_spotify_token(f):
    """
    Decorator para proteger rotas.
    Garante que o token do spotify do usuário esteja 
    atualizado antes de acessar a rota, levando pra
    um refresh forçado se avaliado.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if current_user:
            from app.services.spotify_service import SpotifyService
            SpotifyService.maybe_refresh_token(current_user)
        return f(*args, **kwargs)
    return decorated