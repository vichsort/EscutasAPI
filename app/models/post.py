import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class BlogPostMention(db.Model):
    """Tabela ponte para as menções/tags polimórficas do Blog"""
    __tablename__ = 'blog_post_mentions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey('blog_posts.id', ondelete="CASCADE"), nullable=False)
    
    # Ex: 'REVIEW', 'ARTIST', 'ALBUM', 'TRACK'
    target_type = db.Column(db.String(20), nullable=False, index=True) 
    
    # String(255) para aceitar tanto UUIDs (Reviews) quanto IDs do Spotify
    target_id = db.Column(db.String(255), nullable=False, index=True)
    
    # texto da tag para renderização rápida no Front
    target_name = db.Column(db.String(255), nullable=True) 

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, index=True, nullable=False)
    summary = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=False)
    cover_image_url = db.Column(db.String(500), nullable=True)
    track_metadata = db.Column(db.JSON, default=dict) 
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, PUBLISHED, ARCHIVED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime, nullable=True)
    author = db.relationship('User', backref='posts', lazy=True)
    mentions = db.relationship('BlogPostMention', backref='post', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'slug': self.slug,
            'status': self.status
        }