from typing import List, Optional
from app.extensions import cache, db
from app.schemas import AlbumBase, AlbumFull, TrackBase
from spotipy.exceptions import SpotifyException
from app.services.curation_service import CurationService
from app.services.spotify_service import SpotifyService
from app.services.spotify_sync_service import SpotifySyncService
from app.models.album import Album
from app.models.album_track import AlbumTrack
from app.exceptions import SpotifyAPIError, ResourceNotFoundError
from app.utils import is_canonical_album, is_track_skippable, clean_album_title

class AlbumService:

    @staticmethod
    def search_albums(user, query: str) -> List[AlbumBase]:
        """
        Busca álbuns, aplica o Regex de limpeza e verifica o veredito da comunidade.
        """
        sp = SpotifyService.get_client(user)
        return AlbumService._search_albums_cached(user.spotify_id, query, sp)

    @staticmethod
    @cache.memoize(timeout=3600)
    def _search_albums_cached(spotify_id: str, query: str, sp) -> List[AlbumBase]:
        try:
            results = sp.search(q=query, type='album', limit=10)
            items = results['albums']['items']

            spotify_ids = [item['id'] for item in items]
            community_overrides = CurationService.get_community_overrides(spotify_ids)

            albums_list = []
            for item in items:
                if item.get('album_type') == 'compilation':
                    continue

                raw_name = item['name']
                album_id = item['id']
                cover = item['images'][0]['url'] if item['images'] else None
                regex_decision = is_canonical_album(raw_name)
                final_canonical_status = community_overrides.get(album_id, regex_decision)

                albums_list.append(AlbumBase(
                    id=album_id,
                    name=raw_name,
                    clean_name=clean_album_title(raw_name),
                    artist=", ".join([artist['name'] for artist in item['artists']]),
                    cover_url=cover,
                    release_date=item['release_date'],
                    is_canonical=final_canonical_status
                ))

            return albums_list

        except SpotifyException as e:
            raise SpotifyAPIError(f"Erro na busca de álbuns: {e.msg}")

    @staticmethod
    def get_album_details(user, album_id: str) -> Optional[AlbumFull]:
        """
        Busca detalhes de um album e sugere quais faixas devem ser ignoradas.
        """
        sp = SpotifyService.get_client(user)
        return AlbumService._get_album_details_cached(user.spotify_id, album_id, sp)

    @staticmethod
    @cache.memoize(timeout=604800)
    def _get_album_details_cached(spotify_id: str, album_id: str, sp) -> Optional[AlbumFull]:
        try:
            # Tenta ler do banco primeiro
            album = Album.query.filter_by(spotify_album_id=album_id).first()

            if album and not album.needs_sync():
                tracks_db = AlbumTrack.query.filter_by(
                    album_spotify_id=album_id
                ).order_by(AlbumTrack.track_number).all()

                community_overrides = CurationService.get_community_overrides([album_id])
                final_canonical_status = community_overrides.get(album_id, album.is_canonical)

                return AlbumFull(
                    id=album.spotify_album_id,
                    name=album.name,
                    clean_name=album.clean_name,
                    artist=album.artist_name,
                    cover_url=album.cover_url,
                    release_date=album.release_date,
                    total_tracks=album.total_tracks,
                    is_canonical=final_canonical_status,
                    tracks=[
                        TrackBase(
                            id=t.spotify_track_id,
                            name=t.name,
                            track_number=t.track_number,
                            duration_ms=t.duration_ms,
                            preview_url=t.preview_url,
                            suggested_ignore=is_track_skippable(t.name)
                        ) for t in tracks_db
                    ]
                )

            # Banco vazio ou desatualizado — vai ao Spotify e sincroniza
            album = SpotifySyncService.sync_album(album_id, sp)
            db.session.commit()

            tracks_db = AlbumTrack.query.filter_by(
                album_spotify_id=album_id
            ).order_by(AlbumTrack.track_number).all()

            community_overrides = CurationService.get_community_overrides([album_id])
            final_canonical_status = community_overrides.get(album_id, album.is_canonical)

            return AlbumFull(
                id=album.spotify_album_id,
                name=album.name,
                clean_name=album.clean_name,
                artist=album.artist_name,
                cover_url=album.cover_url,
                release_date=album.release_date,
                total_tracks=album.total_tracks,
                is_canonical=final_canonical_status,
                tracks=[
                    TrackBase(
                        id=t.spotify_track_id,
                        name=t.name,
                        track_number=t.track_number,
                        duration_ms=t.duration_ms,
                        preview_url=t.preview_url,
                        suggested_ignore=is_track_skippable(t.name)
                    ) for t in tracks_db
                ]
            )

        except SpotifyException as e:
            if e.http_status == 404:
                raise ResourceNotFoundError("Álbum")
            raise SpotifyAPIError(f"Erro ao detalhar álbum {album_id}: {e.msg}")