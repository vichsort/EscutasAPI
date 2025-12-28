from functools import wraps
from flask import session
from app.models.user import User
from app.extensions import db
from app.utils.response_util import APIError

def require_auth(f):
    """
    Decorator para proteger rotas.
    Verifica se o usuário tem ID na sessão e se existe no banco local.
    NÃO faz chamadas externas ao Spotify (Performance Otimizada).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id') or session.get('user_uuid')
        
        if not user_id:
            raise APIError("Sessão expirada ou usuário não logado.", 401)
        
        user = db.session.get(User, user_id)
        
        if not user:
            session.clear()
            raise APIError("Usuário não encontrado.", 401)
            
        return f(user, *args, **kwargs)
        
    return decorated_function