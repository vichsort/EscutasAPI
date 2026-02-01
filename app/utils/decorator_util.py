from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User
from app.utils.response_util import APIError

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
            current_user = User.query.get(user_id)
            
            if not current_user:
                raise APIError("Usuário não encontrado.", 401)
                
        except Exception:
            raise APIError("Token inválido ou expirado.", 401)

        return f(current_user, *args, **kwargs)
        
    return decorated