from functools import wraps
from app.services.spotify_service import SpotifyService
from app.models.user import User
from app.extensions import db
from app.utils.response_util import APIError

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        service = SpotifyService()
        sp_client = service.get_client()
        
        if not sp_client:
            raise APIError("Sessão expirada ou usuário não logado.", 401)
        
        # Otimização: Cachear o user_id na sessão para não bater no Spotify/Banco toda vez
        # Mas para simplificar e manter seguro, vamos manter a checagem:
        
        try:
            spotify_user_data = sp_client.current_user()
            spotify_id = spotify_user_data['id']
            
            user = User.query.filter_by(spotify_id=spotify_id).first()
            
            if not user:
                # Auto-cadastro (Lazy registration)
                user = User(
                    spotify_id=spotify_id,
                    display_name=spotify_user_data.get('display_name'),
                    email=spotify_user_data.get('email')
                )
                db.session.add(user)
                db.session.commit()
            
            # Injeta o objeto 'user' nos argumentos da rota original
            return f(user, *args, **kwargs)
            
        except Exception as e:
            raise APIError("Falha na autenticação.", 401)

    return decorated_function