import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    related_review_id = db.Column(UUID(as_uuid=True), db.ForeignKey('album_reviews.id'), nullable=True)
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
    related_review = db.relationship('AlbumReview', backref='related_posts', lazy=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'slug': self.slug,
            'status': self.status
        }