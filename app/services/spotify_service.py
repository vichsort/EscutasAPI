import time
import os
from typing import List, Optional
from collections import Counter
from flask import current_app
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.exceptions import SpotifyException
from app.extensions import db
from app.schemas.album import AlbumBase
from app.schemas.spotify import CurrentPlaybackResponse, SuggestionResponse

# NOSSAS NOVAS EXCEÇÕES
from app.exceptions import SpotifyAPIError, AuthenticationError 

class SpotifyService:
    
    @staticmethod
    def get_oauth_object(redirect_uri=None):
        """
        Cria e retorna um objeto SpotifyOAuth configurado. O redirect_uri pode ser
        passado como argumento ou será lido da variável de ambiente. O cache_handler é configurado
        para usar memória, evitando a necessidade de arquivos de cache. O show_dialog é definido
        como True para garantir que o usuário sempre veja a tela de autorização, mesmo que já tenha autorizado antes.
        """
        if not redirect_uri:
            redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
            
        return SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=redirect_uri,
            scope=current_app.config['SPOTIFY_SCOPE'],
            cache_handler=MemoryCacheHandler(), 
            show_dialog=True
        )

    @staticmethod
    def get_client(user) -> Spotify:
        """
        Retorna cliente Spotify. Se o token não existir ou a renovação falhar,
        dispara AuthenticationError (401).
        """
        if not user or not user.access_token or not user.refresh_token:
            raise AuthenticationError("Usuário não possui credenciais do Spotify válidas.")

        expires_at = user.token_expires_at or 0
        now = int(time.time())
        
        if expires_at - now < 60:
            try:
                sp_oauth = SpotifyService.get_oauth_object()
                new_token_info = sp_oauth.refresh_access_token(user.refresh_token)
                
                user.update_tokens(new_token_info)
                db.session.commit()
            except Exception as e:
                raise AuthenticationError("Sessão do Spotify expirou e não pôde ser renovada.")

        return Spotify(auth=user.access_token)

    @staticmethod
    def _extract_album_object(track_data) -> Optional[AlbumBase]:
        """
        Pega os dados de um álbum e extrai as informações necessárias para criar um objeto 
        AlbumBase. Se os dados do álbum forem inválidos ou ausentes, retorna None.
        """
        album = track_data.get('album')
        if not album: return None
            
        cover = album['images'][0]['url'] if album['images'] else None
        
        return AlbumBase(
            id=album['id'],
            name=album['name'],
            artist=", ".join([artist['name'] for artist in album['artists']]),
            cover_url=cover,
            release_date=album['release_date']
        )

    @staticmethod
    def get_currently_playing(user) -> Optional[CurrentPlaybackResponse]:
        """
        Busca o álbum que está sendo tocado nesse momento pelo usuário.
        """
        sp = SpotifyService.get_client(user)

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
            
        except SpotifyException as e:
            raise SpotifyAPIError(f"Erro na API do Spotify: {e.msg}")

    @staticmethod
    def get_recently_played_suggestions(user, limit=50, threshold=3) -> List[SuggestionResponse]:
        """
        Analisa o histórico recente do usuário para sugerir álbuns que ele tem ouvido com frequência.
        O método busca as últimas faixas tocadas (limit) e conta quantas vezes cada álbum aparece.
        Se um álbum tiver sido ouvido mais vezes do que o threshold, ele é sugerido ao usuário, 
        junto com a razão (quantas faixas do álbum foram ouvidas recentemente).
            OBS. Álbuns de compilação e faixas locais são ignorados.
        """
        sp = SpotifyService.get_client(user)

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

        except SpotifyException as e:
            raise SpotifyAPIError(f"Não foi possível buscar histórico recente: {e.msg}")