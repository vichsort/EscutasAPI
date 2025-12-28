from datetime import datetime, timezone
from app.extensions import db
from app.models.user import User

class AuthService:
    @staticmethod
    def login_or_register_user(spotify_user_data, token_info):
        """
        Recebe dados do Spotify e Tokens.
        Se o usuário existe, atualiza tokens.
        Se não existe, cria.
        Retorna o objeto User.
        """
        spotify_id = spotify_user_data['id']
        
        # 1. Busca usuário no banco
        user = User.query.filter_by(spotify_id=spotify_id).first()
        
        # 2. Se não existir, CRIA
        if not user:
            user = User(
                spotify_id=spotify_id,
                display_name=spotify_user_data.get('display_name'),
                email=spotify_user_data.get('email')
            )
            db.session.add(user)
        
        # 3. Atualiza Tokens (Sempre, para manter o login vivo)
        user.access_token = token_info['access_token']
        user.refresh_token = token_info.get('refresh_token', user.refresh_token)
        user.token_expires_at = int(token_info['expires_at'])
        
        # Atualiza infos básicas caso tenham mudado no Spotify
        user.display_name = spotify_user_data.get('display_name')
        
        db.session.commit()
        
        return user