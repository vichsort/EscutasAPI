from app.extensions import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spotify_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150))
    avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)

    token_expires_at = db.Column(db.Integer, nullable=True)

    # Relacionamento: Um usuário tem muitas avaliações de álbuns
    reviews = db.relationship('AlbumReview', backref='user', lazy=True)

    @property
    def review_count(self):
        """Conta o total de reviews do usuário dinamicamente"""
        from app.models.review import AlbumReview
        return db.session.query(AlbumReview).filter_by(user_id=self.id).count()

    @property
    def platinum_count(self):
        """Conta o total de platinas do usuário dinamicamente"""
        from app.models.platinum import UserPlatinum
        return db.session.query(UserPlatinum).filter_by(user_id=self.id).count()

    @property
    def blog_post_count(self):
        """Conta quantos posts o usuário escreveu no blog"""
        from app.models.post import BlogPost
        return db.session.query(BlogPost).filter_by(author_id=self.id).count()

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