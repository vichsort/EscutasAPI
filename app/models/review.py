from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AlbumReview(db.Model):
    __tablename__ = 'album_reviews'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    # Metadata do Spotify
    spotify_album_id = db.Column(db.String(100), nullable=False, index=True)
    album_name = db.Column(db.String(200), nullable=False)
    artist_name = db.Column(db.String(200), nullable=False)
    cover_url = db.Column(db.String(500))
    
    # Dados da Avaliação
    review_text = db.Column(db.Text, nullable=True)
    average_score = db.Column(db.Float, default=0.0)
    tier = db.Column(db.String(2), default='-')
    
    # Controle de Tempo (Histórico)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento: Uma review tem várias notas de faixas
    tracks = db.relationship('TrackReview', backref='album_review', lazy=True, cascade='all, delete-orphan')

    # NOTA: Removemos o UniqueConstraint. 
    # Agora o usuário pode ter múltiplas linhas com o mesmo spotify_album_id.

    def update_stats(self):
        """Recalcula a média e o Tier baseado nas faixas filhas."""
        if not self.tracks:
            self.average_score = 0.0
            self.tier = '-'
            return

        total = sum([t.score for t in self.tracks])
        count = len(self.tracks)
        self.average_score = round(total / count, 2)
        
        # Lógica de Tier
        if self.average_score >= 9.5: self.tier = 'S'
        elif self.average_score >= 9.0: self.tier = 'A'
        elif self.average_score >= 8.0: self.tier = 'B'
        elif self.average_score >= 7.0: self.tier = 'C'
        elif self.average_score >= 6.0: self.tier = 'D'
        elif self.average_score >= 4.0: self.tier = 'E'
        else: self.tier = 'F'

    def to_dict(self):
        """Helper para serializar para JSON (facilita nas rotas)"""
        return {
            "id": self.id,
            "album_id": self.spotify_album_id,
            "album_name": self.album_name,
            "artist": self.artist_name,
            "cover": self.cover_url,
            "review_text": self.review_text,
            "score": self.average_score,
            "tier": self.tier,
            "created_at": self.created_at.isoformat(),
            "tracks": [t.to_dict() for t in self.tracks]
        }


class TrackReview(db.Model):
    __tablename__ = 'track_reviews'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Vincula a ESTA review específica, não ao álbum genericamente
    album_review_id = db.Column(UUID(as_uuid=True), db.ForeignKey('album_reviews.id'), nullable=False)
    
    # Metadata da Faixa
    spotify_track_id = db.Column(db.String(100), nullable=False)
    track_name = db.Column(db.String(200), nullable=False)
    track_number = db.Column(db.Integer)
    
    # A Nota
    score = db.Column(db.Float, nullable=False)

    # Garante que não haja notas duplicadas PARA A MESMA FAIXA NA MESMA REVIEW
    # (Ex: não posso dar duas notas pra faixa 1 na review de hoje, mas posso dar outra nota na review de amanhã)
    __table_args__ = (
        db.UniqueConstraint('album_review_id', 'spotify_track_id', name='unique_review_track'),
    )

    def to_dict(self):
        return {
            "track_id": self.spotify_track_id,
            "name": self.track_name,
            "number": self.track_number,
            "score": self.score
        }