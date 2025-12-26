import time
from flask import session, current_app
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

class SpotifyService:
    def __init__(self):
        # Inicializa o Auth Manager com configs do app
        self.sp_oauth = SpotifyOAuth(
            client_id=current_app.config['SPOTIFY_CLIENT_ID'],
            client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
            scope=current_app.config['SPOTIFY_SCOPE']
        )

    def get_auth_url(self):
        return self.sp_oauth.get_authorize_url()

    def get_token_from_code(self, code):
        return self.sp_oauth.get_access_token(code)

    def get_client(self):
        """Retorna uma instância do Spotify autenticada ou None."""
        token_info = session.get('token_info', None)
        if not token_info:
            return None

        # Renovação de Token automática
        now = int(time.time())
        is_expired = token_info['expires_at'] - now < 60
        if is_expired:
            token_info = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info

        return Spotify(auth=token_info['access_token'])