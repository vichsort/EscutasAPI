from typing import List, Optional
from app.extensions import cache
from app.services.spotify_service import SpotifyService
from app.schemas.album import AlbumBase, AlbumFull, TrackBase
from spotipy.exceptions import SpotifyException
from app.exceptions import SpotifyAPIError, ResourceNotFoundError
from app.utils.text_util import is_canonical_album, is_track_skippable, clean_album_title

class AlbumService:
    
    @staticmethod
    @cache.memoize(timeout=3600)
    def search_albums(user, query: str) -> List[AlbumBase]:
        """
        Busca álbuns no Spotify.
        Retorna lista de objetos AlbumBase (Pydantic).
        """
        sp = SpotifyService.get_client(user)

        try:
            results = sp.search(q=query, type='album', limit=10)
            albums_list = []
            
            for item in results['albums']['items']:
                if item.get('album_type') == 'compilation': continue 
                
                raw_name = item['name']
                cover = item['images'][0]['url'] if item['images'] else None

                album = AlbumBase(
                    id=item['id'],
                    name=raw_name,
                    clean_name=clean_album_title(raw_name),
                    artist=", ".join([artist['name'] for artist in item['artists']]),
                    cover_url=cover,
                    release_date=item['release_date'],
                    is_canonical=is_canonical_album(raw_name)
                )
                albums_list.append(album)
                
            return albums_list

        except SpotifyException as e:
            raise SpotifyAPIError(f"Erro na busca de álbuns: {e.msg}")

    @staticmethod
    @cache.memoize(timeout=604800)
    def get_album_details(user, album_id: str) -> Optional[AlbumFull]:
        """
        Busca detalhes completos.
        Retorna objeto AlbumFull (Pydantic).
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

            cover = album_data['images'][0]['url'] if album_data['images'] else None

            return AlbumFull(
                id=album_data['id'],
                name=album_data['name'],
                artist=", ".join([a['name'] for a in album_data['artists']]),
                cover_url=cover,
                release_date=album_data['release_date'],
                total_tracks=album_data['total_tracks'],
                tracks=tracks_objects
            )

        except SpotifyException as e:
            if e.http_status == 404:
                raise ResourceNotFoundError("Álbum")
            raise SpotifyAPIError(f"Erro ao detalhar álbum {album_id}: {e.msg}")