from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AlbumReview(db.Model):
    __tablename__ = 'album_reviews'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    # Metadados do Álbum (Desnormalizados para leitura rápida)
    spotify_album_id = db.Column(db.String(100), nullable=False)
    album_name = db.Column(db.String(255), nullable=False)
    artist_name = db.Column(db.String(255), nullable=False)
    cover_url = db.Column(db.String(500))
    
    # Conteúdo da Review
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Stats
    average_score = db.Column(db.Float, default=0.0)
    tier = db.Column(db.String(20), default='C') # S, A, B, C, D, E
    
    # Relacionamento com as faixas
    tracks = db.relationship('TrackReview', backref='album_review', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        # Permite buscar "todas as reviews DO USUÁRIO X, ordenadas por DATA" instantaneamente.
        db.Index('idx_reviews_user_date', 'user_id', 'created_at'),

        # Permite buscar "todas as reviews do álbum Dark Side of the Moon" rapidamente.
        db.Index('idx_reviews_spotify_album', 'spotify_album_id'),
    )

    def update_stats(self):
        """Recalcula a média e o Tier baseada nas faixas."""
        if not self.tracks:
            self.average_score = 0
            self.tier = 'E'
            return

        total = sum(t.score for t in self.tracks)
        self.average_score = round(total / len(self.tracks), 1)
        
        # Define Tier
        if self.average_score >= 9.5: self.tier = 'S'
        elif self.average_score >= 8.5: self.tier = 'A'
        elif self.average_score >= 7.0: self.tier = 'B'
        elif self.average_score >= 5.0: self.tier = 'C'
        elif self.average_score >= 3.0: self.tier = 'D'
        else: self.tier = 'E'

    def to_dict(self):
        return {
            'id': str(self.id),
            'album': {
                'name': self.album_name,
                'artist': self.artist_name,
                'cover': self.cover_url,
                'id': self.spotify_album_id
            },
            'review_text': self.review_text,
            'score': self.average_score,
            'tier': self.tier,
            'created_at': self.created_at.isoformat(),
            'tracks': [t.to_dict() for t in self.tracks]
        }

class TrackReview(db.Model):
    __tablename__ = 'track_reviews'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_review_id = db.Column(UUID(as_uuid=True), db.ForeignKey('album_reviews.id'), nullable=False)
    
    spotify_track_id = db.Column(db.String(100), nullable=False)
    track_name = db.Column(db.String(255), nullable=False)
    track_number = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.track_name,
            'track_number': self.track_number,
            'score': self.score
        }