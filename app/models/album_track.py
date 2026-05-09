import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID

class AlbumTrack(db.Model):
    __tablename__ = 'album_tracks'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_track_id = db.Column(db.String(100), nullable=False, index=True)
    album_spotify_id = db.Column(db.String(100), db.ForeignKey('albums.spotify_album_id'), nullable=False, index=True)
    name = db.Column(db.String(300), nullable=False)
    track_number = db.Column(db.Integer, nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)
    preview_url = db.Column(db.String(500), nullable=True)
    suggested_ignore = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<AlbumTrack {self.name}>'