from app.extensions import cache, db
from app.services.curation_service import CurationService
from app.services.spotify_service import SpotifyService
from app.services.spotify_sync_service import SpotifySyncService
from app.models import AlbumReview, UserPlatinum, Artist, Album
from app.utils import clean_album_title
from app.exceptions import SpotifyAPIError, ResourceNotFoundError
from spotipy.exceptions import SpotifyException

class ArtistService:

    @staticmethod
    def search_artists(user, query: str, limit=10) -> list:
        """
        Busca artistas no Spotify.
        """
        sp = SpotifyService.get_client(user)
        return ArtistService._search_artists_cached(user.spotify_id, query, limit, sp)

    @staticmethod
    @cache.memoize(timeout=3600)
    def _search_artists_cached(spotify_id: str, query: str, limit: int, sp) -> list:
        try:
            results = sp.search(q=query, type='artist', limit=limit)
            artists = []

            for item in results['artists']['items']:
                # Salva artista no banco (aproveita gêneros enquanto API retorna)
                existing = Artist.query.filter_by(spotify_artist_id=item['id']).first()
                if not existing:
                    new_artist = Artist(
                        spotify_artist_id=item['id'],
                        name=item['name'],
                        image_url=item['images'][0]['url'] if item['images'] else None,
                        genres=item.get('genres', []) or []
                    )
                    db.session.add(new_artist)

                artists.append({
                    "id": item['id'],
                    "name": item['name'],
                    "image_url": item['images'][0]['url'] if item['images'] else None,
                    "genres": item.get('genres', [])
                })

            db.session.commit()
            return artists

        except SpotifyException as e:
            raise SpotifyAPIError(f"Erro na busca de artistas: {e.msg}")

    @staticmethod
    def get_platinum_progress(user, artist_id: str):
        """
        Calcula o progresso de Platina de um usuário para um artista específico.
        Também é usado pra construir a página do artista com todas as informações de discografia e progresso.
        """
        sp = SpotifyService.get_client(user)
        return ArtistService._get_platinum_progress_cached(str(user.id), artist_id, sp, user)

    @staticmethod
    @cache.memoize(timeout=3600)
    def _get_platinum_progress_cached(user_id: str, artist_id: str, sp, user) -> dict:
        if not artist_id:
            raise ResourceNotFoundError("Artista")

        try:
            # Sincroniza artista e discografia (respeita needs_sync — só vai ao Spotify se necessário)
            artist = SpotifySyncService.sync_artist_discography(artist_id, sp)

            # Lê discografia do banco
            albums_db = Album.query.filter_by(artist_spotify_id=artist_id).all()
            spotify_ids = [a.spotify_album_id for a in albums_db]
            community_overrides = CurationService.get_community_overrides(spotify_ids)

            canonical_discography = {}

            for album in albums_db:
                clean_name = album.clean_name or clean_album_title(album.name)
                is_canonical = community_overrides.get(album.spotify_album_id, album.is_canonical)

                if clean_name not in canonical_discography:
                    canonical_discography[clean_name] = {
                        "clean_name": clean_name,
                        "cover_url": album.cover_url,
                        "release_date": album.release_date,
                        "is_canonical": is_canonical,
                        "versions": [album.spotify_album_id]
                    }
                else:
                    canonical_discography[clean_name]["versions"].append(album.spotify_album_id)
                    if is_canonical:
                        canonical_discography[clean_name]["is_canonical"] = True

            required_albums = {
                name: data for name, data in canonical_discography.items()
                if data["is_canonical"]
            }

            all_required_version_ids = []
            for data in required_albums.values():
                all_required_version_ids.extend(data["versions"])

            user_reviews = AlbumReview.query.filter(
                AlbumReview.user_id == user.id,
                AlbumReview.spotify_album_id.in_(all_required_version_ids)
            ).all()

            reviewed_spotify_ids = {r.spotify_album_id for r in user_reviews}

            progress_list = []
            completed_count = 0

            for clean_name, data in required_albums.items():
                is_completed = any(vid in reviewed_spotify_ids for vid in data["versions"])
                if is_completed:
                    completed_count += 1

                progress_list.append({
                    "clean_name": clean_name,
                    "cover_url": data["cover_url"],
                    "release_date": data["release_date"][:4],
                    "is_completed": is_completed
                })

            progress_list.sort(key=lambda x: x['release_date'], reverse=True)

            total_required = len(required_albums)
            percentage = round((completed_count / total_required) * 100) if total_required > 0 else 0
            is_platinum = (total_required > 0) and (completed_count == total_required)

            existing_plat = UserPlatinum.query.filter_by(
                user_id=user.id,
                spotify_artist_id=artist_id
            ).first()

            if is_platinum and not existing_plat:
                db.session.add(UserPlatinum(
                    user_id=user.id,
                    spotify_artist_id=artist_id,
                    artist_name=artist.name,
                    artist_image_url=artist.image_url
                ))
                db.session.commit()
            elif not is_platinum and existing_plat:
                db.session.delete(existing_plat)
                db.session.commit()

            return {
                "artist": {
                    "id": artist_id,
                    "name": artist.name,
                    "image_url": artist.image_url
                },
                "stats": {
                    "total_required": total_required,
                    "completed_count": completed_count,
                    "percentage": percentage,
                    "is_platinum": is_platinum
                },
                "discography": progress_list
            }

        except SpotifyException as e:
            if e.http_status == 404:
                raise ResourceNotFoundError("Artista")
            raise SpotifyAPIError(f"Erro ao buscar artista no Spotify: {e.msg}")