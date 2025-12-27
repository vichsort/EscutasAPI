from typing import List, Optional
from app.extensions import cache
from app.services.spotify_service import SpotifyService
from app.schemas.album import AlbumBase, AlbumFull, TrackBase

class AlbumService:
    
    @staticmethod
    @cache.memoize(timeout=3600)
    def search_albums(user, query: str) -> List[AlbumBase]:
        """
        Busca álbuns no Spotify.
        Retorna lista de objetos AlbumBase (Pydantic).
        """
        sp = SpotifyService.get_client(user)
        if not sp: return []

        try:
            results = sp.search(q=query, type='album', limit=20)
            albums_list = []
            
            for item in results['albums']['items']:
                if item.get('album_type') == 'compilation': continue 
                
                cover = item['images'][0]['url'] if item['images'] else None

                album = AlbumBase(
                    spotify_id=item['id'],
                    name=item['name'],
                    artist=", ".join([artist['name'] for artist in item['artists']]),
                    cover_url=cover,
                    release_date=item['release_date']
                )
                albums_list.append(album)
                
            return albums_list

        except Exception as e:
            print(f"Erro na busca de álbuns: {e}")
            return []

    @staticmethod
    @cache.memoize(timeout=604800)
    def get_album_details(user, album_id: str) -> Optional[AlbumFull]:
        """
        Busca detalhes completos.
        Retorna objeto AlbumFull (Pydantic).
        """
        sp = SpotifyService.get_client(user)
        if not sp: return None

        try:
            album_data = sp.album(album_id)

            tracks_objects = []
            for track in album_data['tracks']['items']:
                tracks_objects.append(TrackBase(
                    id=track['id'],
                    name=track['name'],
                    track_number=track['track_number'],
                    duration_ms=track['duration_ms'],
                    preview_url=track['preview_url']
                ))

            cover = album_data['images'][0]['url'] if album_data['images'] else None

            return AlbumFull(
                spotify_id=album_data['id'],
                name=album_data['name'],
                artist=", ".join([a['name'] for a in album_data['artists']]),
                cover_url=cover,
                release_date=album_data['release_date'],
                total_tracks=album_data['total_tracks'],
                label=album_data.get('label'),
                tracks=tracks_objects
            )

        except Exception as e:
            print(f"Erro ao detalhar álbum {album_id}: {e}")
            return None