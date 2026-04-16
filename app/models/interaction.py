import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class Comment(db.Model):
    """
    Tabela polimórfica de comentários. 
    Pode ser usada para comentar em Reviews ou Blog Posts.
    """
    __tablename__ = 'comments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    # Alvo do comentário
    target_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    target_type = db.Column(db.String(20), nullable=False, index=True) # 'REVIEW' ou 'POST'
    
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamento para acessar os dados do autor facilmente
    author = db.relationship('User', backref=db.backref('comments', lazy=True))

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "author_name": self.author.display_name if self.author else "Usuário Removido",
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }

class Vote(db.Model):
    """
    Tabela polimórfica de votos (Upvote/Downvote).
    Pode ser usada para Reviews, Blog Posts e até nos próprios Comentários!
    """
    __tablename__ = 'votes'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    # Alvo do voto
    target_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    target_type = db.Column(db.String(20), nullable=False, index=True) # 'REVIEW', 'POST', 'COMMENT'
    
    # Valor: +1 para Upvote, -1 para Downvote
    value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # Regra de Ouro: Um usuário só pode votar uma vez em cada alvo.
        db.UniqueConstraint('user_id', 'target_id', 'target_type', name='uix_user_interaction_vote'),
    )