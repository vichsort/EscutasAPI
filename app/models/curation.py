from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone

class AlbumCurationVote(db.Model):
    """Guarda os votos da comunidade sobre o que pertence ou não à Platina"""
    __tablename__ = 'album_curation_votes'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    spotify_album_id = db.Column(db.String(100), nullable=False, index=True)
    
    # True = "Faz parte da Platina" | False = "Ignorar da Platina"
    is_canonical = db.Column(db.Boolean, nullable=False) 
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # Garante que um usuário só tenha UM voto ativo por álbum. 
        # Se ele mudar de ideia, nós atualizamos a mesma linha.
        db.UniqueConstraint('user_id', 'spotify_album_id', name='uix_user_album_vote'),
    )