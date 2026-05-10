import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class CustomAlbum(db.Model):
    __tablename__ = 'custom_albums'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(300), nullable=False)
    artist_name = db.Column(db.String(200), nullable=False)
    cover_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship('User', backref=db.backref('custom_albums', lazy=True))

    @property
    def spotify_album_id(self):
        """Gera o ID no formato custom:uuid pra compatibilidade com o resto do sistema."""
        return f"custom:{self.id}"

    def __repr__(self):
        return f'<CustomAlbum {self.name}>'