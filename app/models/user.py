from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento: Um usuário tem muitas avaliações de álbuns
    reviews = db.relationship('AlbumReview', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.display_name}>'