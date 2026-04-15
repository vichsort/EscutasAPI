from app.extensions import db
from app.models import User
from app.services.spotify_service import SpotifyService
from flask_jwt_extended import create_access_token
import spotipy

class AuthService:
    
    @staticmethod
    def execute_login(code: str, redirect_uri: str):
        """
        Orquestra todo o fluxo de login:
        1. Troca CODE por Token Spotify.
        2. Busca dados do User no Spotify.
        3. Cria ou Atualiza User no Banco.
        4. Gera o Token JWT.
        
        Retorna: tupla (user, api_access_token)
        """
        
        sp_oauth = SpotifyService.get_oauth_object(redirect_uri=redirect_uri)
        token_info = sp_oauth.get_access_token(code)
        
        if not token_info:
            raise ValueError("Falha ao obter token do Spotify")

        sp = spotipy.Spotify(auth=token_info['access_token'])
        spotify_user_data = sp.current_user()
        user = AuthService._upsert_user(spotify_user_data, token_info)
        api_access_token = create_access_token(identity=str(user.id))
        
        return user, api_access_token

    @staticmethod
    def _upsert_user(spotify_data, token_info):
        """Lida com a criação ou atualização do usuário após o login"""
        spotify_id = spotify_data['id']
        
        user = User.query.filter_by(spotify_id=spotify_id).first()
        
        if not user:
            user = User(
                spotify_id=spotify_id,
                display_name=spotify_data.get('display_name')
            )
            db.session.add(user)
        
        # Atualiza o nome (caso o usuário tenha mudado no Spotify)
        user.display_name = spotify_data.get('display_name')
        
        # Captura a URL da imagem (pega a primeira da lista, se existir)
        images = spotify_data.get('images')
        if images and len(images) > 0:
            user.avatar_url = images[0]['url']

        # Atualiza tokens
        user.access_token = token_info['access_token']
        user.refresh_token = token_info.get('refresh_token', user.refresh_token)
        user.token_expires_at = token_info['expires_at']
        
        db.session.commit()
        return user