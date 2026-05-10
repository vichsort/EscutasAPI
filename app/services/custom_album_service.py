from app.extensions import db
from app.models.custom_album import CustomAlbum
from app.models.custom_album_track import CustomAlbumTrack
from app.schemas.album import CustomAlbumOutput, AlbumFull, TrackBase
from app.exceptions import ResourceNotFoundError
import uuid

class CustomAlbumService:

    @staticmethod
    def create_custom_album(user, payload) -> CustomAlbumOutput:
        album = CustomAlbum(
            user_id=user.id,
            name=payload.name,
            artist_name=payload.artist_name,
            cover_url=payload.cover_url
        )
        db.session.add(album)
        db.session.flush()

        for track_data in payload.tracks:
            db.session.add(CustomAlbumTrack(
                custom_album_id=album.id,
                name=track_data.name,
                track_number=track_data.track_number,
                duration_ms=track_data.duration_ms
            ))

        db.session.commit()
        return CustomAlbumOutput.model_validate(album)

    @staticmethod
    def get_custom_album(album_id: str) -> AlbumFull:
        """
        Recebe custom:uuid, extrai o UUID e busca no banco.
        Retorna AlbumFull pra ser compatível com o fluxo normal.
        """
        try:
            raw_id = album_id.removeprefix('custom:')
            parsed_id = uuid.UUID(raw_id)
        except ValueError:
            raise ResourceNotFoundError("Álbum customizado")

        album = CustomAlbum.query.filter_by(id=parsed_id).first()
        if not album:
            raise ResourceNotFoundError("Álbum customizado")

        tracks = CustomAlbumTrack.query.filter_by(
            custom_album_id=album.id
        ).order_by(CustomAlbumTrack.track_number).all()

        return AlbumFull(
            id=album.spotify_album_id,
            name=album.name,
            clean_name=album.name,
            artist=album.artist_name,
            cover_url=album.cover_url,
            release_date=None,
            total_tracks=len(tracks),
            is_canonical=False,
            tracks=[
                TrackBase(
                    id=str(t.id),
                    name=t.name,
                    track_number=t.track_number,
                    duration_ms=t.duration_ms or 0,
                    preview_url=None,
                    suggested_ignore=False
                ) for t in tracks
            ]
        )