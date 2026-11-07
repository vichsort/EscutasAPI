import time
import os
from typing import List, Optional
from collections import Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError, ResponseError
from flask import current_app
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.exceptions import SpotifyException
from app.extensions import db, cache
from app.schemas import AlbumBase, CurrentPlaybackResponse, SuggestionResponse
from app.exceptions import SpotifyAPIError, AuthenticationError, SpotifyRateLimitError
from app.constants import SPOTIFY_MAX_RETRY_AFTER


class _SpotifyRetry(Retry):
    """
    Retry do urllib3 que não fica dormindo em 429 longos.
    O spotipy por padrão respeita qualquer Retry-After, então uma cota estourada
    (QUOTA_EXCEEDED) pode prender o worker por muito tempo. Aqui só esperamos
    Retry-After curtos (rate limit comum); senão desistimos na hora e, com
    raise_on_status=False, a resposta volta para o spotipy ler o corpo e o 'reason'.
    """
    def increment(self, method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None):
        if response is not None and response.status == 429:
            retry_after = self.get_retry_after(response)
            if retry_after is None or retry_after > SPOTIFY_MAX_RETRY_AFTER:
                raise MaxRetryError(_pool, url, ResponseError("429 sem Retry-After curto"))
        return super().increment(method, url, response, error, _pool, _stacktrace)


def _build_requests_session() -> requests.Session:
    """Mesma configuração de retry do spotipy, trocando o Retry pelo _SpotifyRetry."""
    retry = _SpotifyRetry(
        total=Spotify.max_retries,
        connect=None,
        read=False,
        allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE']),
        status=Spotify.max_retries,
        backoff_factor=0.3,
        status_forcelist=Spotify.default_retry_codes,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class EscutasSpotify(Spotify):
    """
    Cliente do Spotify do app: retry com teto no Retry-After e 429 convertido em
    SpotifyRateLimitError (503 para o front, com retry_after no corpo).
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('requests_session', _build_requests_session())
        super().__init__(*args, **kwargs)

    def _internal_call(self, method, url, payload, params):
        try:
            return super()._internal_call(method, url, payload, params)
        except SpotifyException as e:
            if e.http_status != 429:
                raise

            quota_exceeded = e.reason == 'QUOTA_EXCEEDED'
            try:
                retry_after = int(e.headers.get('Retry-After'))
            except (TypeError, ValueError):
                retry_after = None

            current_app.logger.warning(
                f"[spotify_429] {method} {url} | quota_exceeded={quota_exceeded} "
                f"retry_after={retry_after} reason={e.reason}"
            )
            raise SpotifyRateLimitError(quota_exceeded=quota_exceeded, retry_after=retry_after) from e


class SpotifyService:
    _client_cache: dict = {}
    
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
            return EscutasSpotify(client_credentials_manager=client_credentials_manager)

        # Modo Usuário Logado
        if not user.access_token or not user.refresh_token:
            raise AuthenticationError("Usuário não possui credenciais do Spotify válidas.")

        expires_at = user.token_expires_at or 0
        now = int(time.time())

        if user.spotify_id not in SpotifyService._client_cache:
            SpotifyService._client_cache[user.spotify_id] = EscutasSpotify(auth=user.access_token)

        return SpotifyService._client_cache[user.spotify_id]
    
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
    @cache.memoize(timeout=600)
    def get_now_playing(user) -> Optional[CurrentPlaybackResponse]:
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
    @cache.memoize(timeout=600)
    def get_suggestions(user, limit=50, threshold=3) -> List[SuggestionResponse]:
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
    @cache.memoize(timeout=600)
    def get_user_top_artists(user, limit=5, time_range='short_term'):
        """
        Retorna os artistas que o usuário mais ouviu recentemente.
        time_range: 'short_term' (4 semanas), 'medium_term' (6 meses), 'long_term' (anos)
        """
        sp = SpotifyService.get_client(user)
        results = sp.current_user_top_artists(limit=limit, time_range=time_range)
        return results['items']

    @staticmethod
    @cache.memoize(timeout=172800)
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
    def create_user_playlist(user, name: str, description: str, public: bool = True):
        """
        Cria uma nova playlist na conta do usuário logado (POST /me/playlists).
        Precisa do token do usuário: o Client Credentials não tem acesso a contas.
        Retorna o ID da playlist criada.
        """
        sp = SpotifyService.get_client(user)

        try:
            playlist = sp.current_user_playlist_create(
                name=name,
                public=public,
                description=description
            )
            return playlist['id']
        except Exception as e:
            current_app.logger.error(f"[spotify_playlist] erro ao criar playlist para user={user.id}: {repr(e)}")
            return None

    @staticmethod
    def add_tracks_to_playlist(user, playlist_id: str, track_uris: list):
        """
        Adiciona uma lista de músicas (URIs) a uma playlist do usuário (POST /playlists/{id}/items).
        track_uris deve ser uma lista no formato: ['spotify:track:ID1', 'spotify:track:ID2']
        """
        if not track_uris:
            return True

        sp = SpotifyService.get_client(user)

        try:
            # O Spotify aceita no máximo 100 itens por requisição
            for i in range(0, len(track_uris), 100):
                sp.playlist_add_items(playlist_id=playlist_id, items=track_uris[i:i + 100])
            return True
        except Exception as e:
            current_app.logger.error(f"[spotify_playlist] erro ao adicionar faixas na playlist={playlist_id}: {repr(e)}")
            return False

    @staticmethod
    def maybe_refresh_token(user):
        expires_at = user.token_expires_at or 0
        now = int(time.time())

        if expires_at - now < 60:
            # Loga o estado antes de tentar
            current_app.logger.warning(
                f"[spotify_refresh] token expirado/expirando para user={user.id} | "
                f"expires_at={expires_at} now={now} diff={expires_at - now}s | "
                f"refresh_token_presente={bool(user.refresh_token)}"
            )

            if not user.refresh_token:
                # Não tenta o refresh, já sabe que vai falhar
                current_app.logger.error(
                    f"[spotify_refresh] refresh_token ausente para user={user.id}"
                )
                raise AuthenticationError(
                    "Sessão do Spotify expirou. Faça login novamente."
                )

            try:
                sp_oauth = SpotifyService.get_oauth_object()
                new_token_info = sp_oauth.refresh_access_token(user.refresh_token)

                # Spotipy retorna None silenciosamente em falha — verifica explicitamente
                if not new_token_info:
                    current_app.logger.error(
                        f"[spotify_refresh] refresh retornou None para user={user.id} | "
                        f"refresh_token={user.refresh_token[:10]}..."
                    )
                    raise AuthenticationError(
                        "Sessão do Spotify expirou e não pôde ser renovada."
                    )

                user.update_tokens(new_token_info)
                db.session.commit()
                SpotifyService._client_cache.pop(user.spotify_id, None)

                current_app.logger.info(
                    f"[spotify_refresh] token renovado com sucesso para user={user.id} | "
                    f"novo expires_at={new_token_info.get('expires_at')}"
                )

            except AuthenticationError:
                # Re-lança sem envolver num segundo raise
                raise

            except Exception as e:
                # Captura SpotifyOauthError, HTTPError, etc — loga o motivo real
                current_app.logger.error(
                    f"[spotify_refresh] exceção ao renovar token para user={user.id}: {repr(e)}"
                )
                raise AuthenticationError(
                    "Sessão do Spotify expirou e não pôde ser renovada."
                ) from e