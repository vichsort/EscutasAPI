import uuid
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import String

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_artist_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    genres = db.Column(ARRAY(String), nullable=True)
    genres_synced_at = db.Column(db.DateTime, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    albums = db.relationship('Album', backref='artist', lazy=True)

    def needs_sync(self, days=30) -> bool:
        if not self.last_synced_at:
            return True
        delta = datetime.now(timezone.utc) - self.last_synced_at.replace(tzinfo=timezone.utc)
        return delta.days >= days

    def __repr__(self):
        return f'<Artist {self.name}>'