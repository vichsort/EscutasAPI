from typing import List, Optional
from app.extensions import cache
from app.schemas import AlbumBase, AlbumFull, TrackBase
from spotipy.exceptions import SpotifyException
from app.services import CurationService, SpotifyService
from app.exceptions import SpotifyAPIError, ResourceNotFoundError
from app.utils import is_canonical_album, is_track_skippable, clean_album_title

class AlbumService:
    
    @staticmethod
    @cache.memoize(timeout=3600)
    def search_albums(user, query: str) -> List[AlbumBase]:
        """
        Busca álbuns, aplica o Regex de limpeza e verifica o veredito da comunidade.
        """
        sp = SpotifyService.get_client(user)

        try:
            results = sp.search(q=query, type='album', limit=10)
            items = results['albums']['items']
            
            # Coleta todos os IDs que o Spotify retornou
            spotify_ids = [item['id'] for item in items]
            
            # Pergunta ao banco de dados: "Tem algum override da comunidade pra esses IDs?"
            # Vai retornar algo como: {'id_123': False, 'id_456': True}
            community_overrides = CurationService.get_community_overrides(spotify_ids)

            albums_list = []
            for item in items:
                if item.get('album_type') == 'compilation': continue 
                
                raw_name = item['name']
                album_id = item['id']
                cover = item['images'][0]['url'] if item['images'] else None

                # O Regex dá o palpite dele...
                regex_decision = is_canonical_album(raw_name)
                
                # ... mas a Comunidade tem a palavra final
                final_canonical_status = community_overrides.get(album_id, regex_decision)

                album = AlbumBase(
                    id=album_id,
                    name=raw_name,
                    clean_name=clean_album_title(raw_name),
                    artist=", ".join([artist['name'] for artist in item['artists']]),
                    cover_url=cover,
                    release_date=item['release_date'],
                    is_canonical=final_canonical_status
                )
                albums_list.append(album)
                
            return albums_list

        except SpotifyException as e:
            raise SpotifyAPIError(f"Erro na busca de álbuns: {e.msg}")

    @staticmethod
    @cache.memoize(timeout=604800)
    def get_album_details(user, album_id: str) -> Optional[AlbumFull]:
        """
        Busca detalhes e sugere quais faixas devem ser ignoradas.
        """
        sp = SpotifyService.get_client(user)

        try:
            album_data = sp.album(album_id)

            tracks_objects = []
            for track in album_data['tracks']['items']:
                track_name = track['name']
                
                tracks_objects.append(TrackBase(
                    id=track['id'],
                    name=track_name,
                    track_number=track['track_number'],
                    duration_ms=track['duration_ms'],
                    preview_url=track['preview_url'],
                    suggested_ignore=is_track_skippable(track_name)
                ))

            raw_name = album_data['name']
            cover = album_data['images'][0]['url'] if album_data['images'] else None
            community_overrides = CurationService.get_community_overrides([album_data['id']])
            final_canonical_status = community_overrides.get(album_data['id'], is_canonical_album(raw_name))

            return AlbumFull(
                id=album_data['id'],
                name=raw_name,
                clean_name=clean_album_title(raw_name),
                artist=", ".join([a['name'] for a in album_data['artists']]),
                cover_url=cover,
                release_date=album_data['release_date'],
                total_tracks=album_data['total_tracks'],
                is_canonical=final_canonical_status,
                tracks=tracks_objects
            )

        except SpotifyException as e:
            if e.http_status == 404:
                raise ResourceNotFoundError("Álbum")
            raise SpotifyAPIError(f"Erro ao detalhar álbum {album_id}: {e.msg}")