from datetime import datetime, timezone
from app.extensions import db
from app.services.spotify_service import SpotifyService
from app.models import Artist, Album, AlbumTrack
from app.utils import is_canonical_album, clean_album_title
from app.exceptions import SpotifyAPIError

class SpotifySyncService:

    @staticmethod
    def sync_artist(spotify_artist_id: str, sp=None) -> Artist:
        """
        Busca ou cria um Artist no banco.
        Só vai ao Spotify se não existir ou se needs_sync() for True.
        """
        try: 
            artist = Artist.query.filter_by(spotify_artist_id=spotify_artist_id).first()

            if artist and not artist.needs_sync():
                return artist

            if not sp:
                sp = SpotifyService.get_client()

            data = sp.artist(spotify_artist_id)

            if not artist:
                artist = Artist(spotify_artist_id=spotify_artist_id)
                db.session.add(artist)

            artist.name = data['name']
            artist.image_url = data['images'][0]['url'] if data['images'] else None
            artist.genres = data.get('genres', []) or []
            artist.genres_synced_at = datetime.now(timezone.utc)
            artist.last_synced_at = datetime.now(timezone.utc)

            db.session.flush()
            return artist
        except Exception as e:
            db.session.rollback()
            raise SpotifyAPIError(f"Erro ao sincronizar artista {spotify_artist_id}: {str(e)}")

    @staticmethod
    def sync_album(spotify_album_id: str, sp=None) -> Album:
        """
        Busca ou cria um Album no banco com suas tracks.
        Só vai ao Spotify se não existir ou se needs_sync() for True.
        """
        try:
            album = Album.query.filter_by(spotify_album_id=spotify_album_id).first()

            if album and not album.needs_sync():
                return album

            if not sp:
                sp = SpotifyService.get_client()

            data = sp.album(spotify_album_id)

            if not album:
                album = Album(spotify_album_id=spotify_album_id)
                db.session.add(album)

            raw_name = data['name']
            artist_spotify_id = data['artists'][0]['id'] if data['artists'] else None

            album.name = raw_name
            album.clean_name = clean_album_title(raw_name)
            album.artist_name = ", ".join([a['name'] for a in data['artists']])
            album.artist_spotify_id = artist_spotify_id
            album.cover_url = data['images'][0]['url'] if data['images'] else None
            album.release_date = data['release_date']
            album.total_tracks = data['total_tracks']
            album.is_canonical = is_canonical_album(raw_name)
            album.last_synced_at = datetime.now(timezone.utc)

            # Herda gêneros do artista se existir no banco
            if artist_spotify_id:
                artist = Artist.query.filter_by(spotify_artist_id=artist_spotify_id).first()
                if artist and artist.genres:
                    album.genres = artist.genres

            # Sincroniza tracks com paginação
            db.session.flush()
            SpotifySyncService._sync_tracks(album, data['tracks'], sp)

            return album
        except Exception as e:
            db.session.rollback()
            raise SpotifyAPIError(f"Erro ao sincronizar álbum {spotify_album_id}: {str(e)}")
            
    @staticmethod
    def _sync_tracks(album: Album, tracks_data: dict, sp) -> None:
        """
        Deleta as tracks antigas e reinsere as atuais.
        """
        AlbumTrack.query.filter_by(album_spotify_id=album.spotify_album_id).delete()

        while True:
            for track in tracks_data['items']:
                db.session.add(AlbumTrack(
                    spotify_track_id=track['id'],
                    album_spotify_id=album.spotify_album_id,
                    name=track['name'],
                    track_number=track['track_number'],
                    duration_ms=track['duration_ms'],
                    preview_url=track['preview_url'],
                    suggested_ignore=False
                ))

            if not tracks_data['next']:
                break

            tracks_data = sp.next(tracks_data)

    @staticmethod
    def sync_artist_discography(spotify_artist_id: str, sp=None) -> Artist:
        """
        Sincroniza artista + discografia completa de estúdio.
        Respeita needs_sync(30 dias) — não vai ao Spotify se estiver fresco.
        """
        try:
            artist = SpotifySyncService.sync_artist(spotify_artist_id, sp)

            if not artist.needs_sync():
                return artist

            if not sp:
                sp = SpotifyService.get_client()

            results = sp.artist_albums(spotify_artist_id, album_type='album', limit=50)
            all_albums = results['items']

            while results['next']:
                results = sp.next(results)
                all_albums.extend(results['items'])

            for item in all_albums:
                if item.get('album_type') == 'compilation':
                    continue
                SpotifySyncService.sync_album(item['id'], sp)

            db.session.commit()
            return artist
        except Exception as e:
            db.session.rollback()
            raise SpotifyAPIError(f"Erro ao sincronizar discografia {spotify_artist_id}: {str(e)}")