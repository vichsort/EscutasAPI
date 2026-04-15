from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

class UserPlatinum(db.Model):
    """Armazena as medalhas de Platina (Discografia 100% concluída) dos usuários."""
    __tablename__ = 'user_platinums'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    spotify_artist_id = db.Column(db.String(100), nullable=False)
    artist_name = db.Column(db.String(255), nullable=False)
    artist_image_url = db.Column(db.String(500), nullable=True)
    
    achieved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # Garante que o usuário não ganhe duas medalhas repetidas da mesma banda
        db.UniqueConstraint('user_id', 'spotify_artist_id', name='uix_user_artist_platinum'),
    )