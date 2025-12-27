import time
from flask import session, current_app
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter

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

    @staticmethod
    def _extract_album_data(track_data):
        """
        Helper privado para limpar o JSON do Spotify e pegar só o que importa.
        """
        album = track_data.get('album')
        if not album:
            return None
            
        # Pega a maior imagem disponível
        cover = album['images'][0]['url'] if album['images'] else None
        
        return {
            "spotify_id": album['id'],
            "name": album['name'],
            "artist": ", ".join([artist['name'] for artist in album['artists']]),
            "cover_url": cover,
            "release_date": album['release_date'],
            "total_tracks": album['total_tracks']
        }

    @staticmethod
    def get_currently_playing(user):
        """
        Busca o que está tocando agora.
        Retorna None se não tiver nada ou se for Podcast/Local.
        """
        sp = SpotifyService.get_client(user)
        if not sp: return None

        try:
            current = sp.current_user_playing_track()
            
            # Se não estiver ouvindo nada ou se não for música (ex: podcast)
            if not current or not current.get('item') or current['currently_playing_type'] != 'track':
                return None
            
            track = current['item']
            
            # Filtro de arquivo local (MP3 no PC do usuário)
            if track.get('is_local'):
                return None

            return {
                "is_playing": current['is_playing'],
                "track_name": track['name'],
                "album": SpotifyService._extract_album_data(track)
            }
            
        except Exception as e:
            print(f"Erro ao buscar currently playing: {e}")
            return None

    @staticmethod
    def get_recently_played_suggestions(user, limit=50, threshold=3):
        """
        Busca histórico, agrupa por álbum e sugere se ouviu >= threshold músicas.
        """
        sp = SpotifyService.get_client(user)
        if not sp: return []

        try:
            # Busca as últimas 50 faixas
            results = sp.current_user_recently_played(limit=limit)
            items = results.get('items', [])
            
            album_counts = Counter()
            album_objects = {}
            
            # 1. Processamento e Contagem
            for item in items:
                track = item.get('track')
                
                # Filtros de Qualidade
                if not track or track.get('is_local') or item.get('context') is None:
                    continue
                
                album = track.get('album')
                if not album or album.get('album_type') == 'compilation': 
                    # Opcional: Ignorar compilações "Vários Artistas" se quiser
                    continue
                
                album_id = album['id']
                album_counts[album_id] += 1
                
                # Guarda o objeto do álbum na primeira vez que vê
                if album_id not in album_objects:
                    album_objects[album_id] = SpotifyService._extract_album_data(track)

            # 2. Filtragem pela Regra de Ouro (Mínimo 3 faixas)
            suggestions = []
            for album_id, count in album_counts.items():
                if count >= threshold:
                    data = album_objects[album_id]
                    data['reason'] = f"Você ouviu {count} faixas recentemente"
                    suggestions.append(data)
            
            return suggestions

        except Exception as e:
            print(f"Erro ao buscar suggestions: {e}")
            return []