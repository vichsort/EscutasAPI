import time
from typing import List, Optional
from collections import Counter
from flask import current_app
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
from app.extensions import db
from app.schemas.album import AlbumBase
from app.schemas.spotify import CurrentPlaybackResponse, SuggestionResponse

class SpotifyService:
    
    @staticmethod
    def get_oauth_object():
        """
        Fábrica do objeto de autenticação OAuth.
        Usa MemoryCacheHandler para evitar criar arquivos .cache no servidor.
        """
        return SpotifyOAuth(
            client_id=current_app.config['SPOTIFY_CLIENT_ID'],
            client_secret=current_app.config['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=current_app.config['SPOTIFY_REDIRECT_URI'],
            scope=current_app.config['SPOTIFY_SCOPE'],
            cache_handler=MemoryCacheHandler(), 
            show_dialog=True
        )

    @staticmethod
    def get_client(user):
        """
        Retorna uma instância do cliente Spotify pronta para uso.
        Gerencia automaticamente a renovação do token (Refresh Token) se necessário.
        
        Args:
            user (User): Objeto do modelo User (SQLAlchemy).
        """
        if not user or not user.access_token or not user.refresh_token:
            return None

        expires_at = user.token_expires_at or 0
        now = int(time.time())
        
        if expires_at - now < 60:
            print(f"--> [SpotifyService] Token de {user.display_name} expirou. Renovando...")
            try:
                sp_oauth = SpotifyService.get_oauth_object()
                new_token_info = sp_oauth.refresh_access_token(user.refresh_token)
                
                user.update_tokens(new_token_info)
                db.session.commit()
                print("--> [SpotifyService] Token renovado e salvo!")
                
            except Exception as e:
                print(f"--> [SpotifyService] Erro crítico ao renovar token: {e}")
                return None

        return Spotify(auth=user.access_token)

    @staticmethod
    def _extract_album_object(track_data) -> Optional[AlbumBase]:
        """
        Helper privado: Converte dados brutos do Spotify no nosso Schema AlbumBase.
        """
        album = track_data.get('album')
        if not album: return None
            
        cover = album['images'][0]['url'] if album['images'] else None
        
        return AlbumBase(
            spotify_id=album['id'],
            name=album['name'],
            artist=", ".join([artist['name'] for artist in album['artists']]),
            cover_url=cover,
            release_date=album['release_date']
        )

    @staticmethod
    def get_currently_playing(user) -> Optional[CurrentPlaybackResponse]:
        """
        Busca o que está tocando. Retorna um objeto tipado ou None.
        """
        sp = SpotifyService.get_client(user)
        if not sp: return None

        try:
            current = sp.current_user_playing_track()
            
            if not current or not current.get('item') or current['currently_playing_type'] != 'track':
                return None
            
            track = current['item']
            if track.get('is_local'): return None

            return CurrentPlaybackResponse(
                is_playing=current['is_playing'],
                track_name=track['name'],
                album=SpotifyService._extract_album_object(track)
            )
            
        except Exception as e:
            print(f"Erro ao buscar currently playing: {e}")
            return None

    @staticmethod
    def get_recently_played_suggestions(user, limit=50, threshold=3) -> List[SuggestionResponse]:
        """
        Algoritmo de Sugestão: Agrupa histórico recente e sugere álbuns repetidos.
        """
        sp = SpotifyService.get_client(user)
        if not sp: return []

        try:
            results = sp.current_user_recently_played(limit=limit)
            items = results.get('items', [])
            
            album_counts = Counter()
            album_objects = {}
            
            for item in items:
                track = item.get('track')
                if not track or track.get('is_local') or item.get('context') is None:
                    continue
                
                album_raw = track.get('album')
                if not album_raw or album_raw.get('album_type') == 'compilation': 
                    continue
                
                album_id = album_raw['id']
                album_counts[album_id] += 1

                if album_id not in album_objects:
                    album_objects[album_id] = SpotifyService._extract_album_object(track)

            suggestions = []
            
            for album_id, count in album_counts.items():
                if count >= threshold:
                    base_album = album_objects[album_id]
                    
                    if base_album:
                        suggestion = SuggestionResponse(
                            **base_album.model_dump(),
                            reason=f"Você ouviu {count} faixas recentemente"
                        )
                        suggestions.append(suggestion)
            
            return suggestions

        except Exception as e:
            print(f"Erro ao buscar suggestions: {e}")
            return []