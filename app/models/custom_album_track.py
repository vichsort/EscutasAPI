import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class CustomAlbumTrack(db.Model):
    __tablename__ = 'custom_album_tracks'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    custom_album_id = db.Column(UUID(as_uuid=True), db.ForeignKey('custom_albums.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(300), nullable=False)
    track_number = db.Column(db.Integer, nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<CustomAlbumTrack {self.name}>'