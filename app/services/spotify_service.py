import time
import os
from typing import List, Optional
from collections import Counter
from flask import current_app
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.exceptions import SpotifyException
from app.extensions import db
from app.schemas import AlbumBase, CurrentPlaybackResponse, SuggestionResponse
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
    def get_client(user=None) -> Spotify:
        """
        Retorna cliente Spotify. 
        Se 'user' for None, usa o modo genérico da aplicação (Client Credentials Flow).
        Se 'user' for fornecido, usa o token dele e renova se necessário.
        """
        # Modo Genérico (Usado pelo BlogService, buscas deslogadas, etc)
        if not user:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
            )
            return Spotify(client_credentials_manager=client_credentials_manager)

        # Modo Usuário Logado
        if not user.access_token or not user.refresh_token:
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

    @staticmethod
    def get_user_top_artists(user, limit=5, time_range='short_term'):
        """
        Retorna os artistas que o usuário mais ouviu recentemente.
        time_range: 'short_term' (4 semanas), 'medium_term' (6 meses), 'long_term' (anos)
        """
        sp = SpotifyService.get_client(user)
        results = sp.current_user_top_artists(limit=limit, time_range=time_range)
        return results['items']

    @staticmethod
    def get_artist_genres(user, artist_id: str) -> list:
        """
        Busca os gêneros musicais de um artista no Spotify.
        """
        if not artist_id:
            return []
            
        sp = SpotifyService.get_client(user)
        try:
            artist_info = sp.artist(artist_id)
            return artist_info.get('genres', [])
        except Exception as e:
            print(f"Erro ao buscar gêneros: {e}")
            return []

    @staticmethod
    def create_user_playlist(user_spotify_id: str, name: str, description: str, public: bool = True):
        """
        Cria uma nova playlist na conta do usuário do Spotify.
        Retorna o ID da playlist criada.
        """
        sp = SpotifyService.get_client()
        if not sp:
            return None

        try:
            playlist = sp.user_playlist_create(
                user=user_spotify_id,
                name=name,
                public=public,
                description=description
            )
            return playlist['id']
        except Exception as e:
            print(f"Erro ao criar playlist no Spotify: {e}")
            return None

    @staticmethod
    def add_tracks_to_playlist(playlist_id: str, track_uris: list):
        """
        Adiciona uma lista de músicas (URIs) a uma playlist específica.
        track_uris deve ser uma lista no formato: ['spotify:track:ID1', 'spotify:track:ID2']
        """
        sp = SpotifyService.get_client()
        if not sp:
            return False

        if not track_uris:
            return True

        try:
            # O Spotify aceita no máximo 100 músicas por vez
            # Se a lista for maior, o Spotipy lida com isso ou podemos fatiar.
            sp.playlist_add_items(playlist_id=playlist_id, items=track_uris)
            return True
        except Exception as e:
            print(f"Erro ao adicionar faixas à playlist: {e}")
            return False