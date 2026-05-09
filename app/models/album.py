import uuid
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import String

class Album(db.Model):
    __tablename__ = 'albums'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_album_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(300), nullable=False)
    clean_name = db.Column(db.String(300), nullable=True)
    artist_name = db.Column(db.String(200), nullable=False)
    artist_spotify_id = db.Column(db.String(100), db.ForeignKey('artists.spotify_artist_id'), nullable=True, index=True)
    cover_url = db.Column(db.String(500), nullable=True)
    release_date = db.Column(db.String(20), nullable=True)
    total_tracks = db.Column(db.Integer, nullable=True)
    is_canonical = db.Column(db.Boolean, default=True)
    genres = db.Column(ARRAY(String), nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tracks = db.relationship('AlbumTrack', backref='album', lazy=True)

    def needs_sync(self, days=30) -> bool:
        if not self.last_synced_at:
            return True
        delta = datetime.now(timezone.utc) - self.last_synced_at.replace(tzinfo=timezone.utc)
        return delta.days >= days

    def __repr__(self):
        return f'<Album {self.name}>'