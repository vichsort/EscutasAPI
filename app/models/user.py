from app.extensions import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.Integer, nullable=True)

    # Relacionamento: Um usuário tem muitas avaliações de álbuns
    reviews = db.relationship('AlbumReview', backref='user', lazy=True)

    def update_tokens(self, token_info):
        """
        Atualiza os tokens e o tempo de expiração de forma centralizada.
        """
        self.access_token = token_info['access_token']
        # O refresh token nem sempre vem na renovação, então só atualizamos se vier
        if token_info.get('refresh_token'):
            self.refresh_token = token_info['refresh_token']
        self.token_expires_at = token_info['expires_at']

    def __repr__(self):
        return f'<User {self.display_name}>'