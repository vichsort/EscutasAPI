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

    @property
    def ranks(self):
        """
        Calcula e retorna os ranks/badges do usuário dinamicamente
        com base nas constantes e estatísticas atuais.
        """
        from app.constants import USER_RANKS
        
        user_ranks = {}
        
        def get_rank_title(category, count):
            """Função auxiliar para varrer os levels e achar o título correto."""
            levels = USER_RANKS.get(category, {})
            # Começa verificando do maior pro menor
            if count >= levels.get('LEVEL_3', {}).get('min', float('inf')): 
                return levels['LEVEL_3']['title']
            if count >= levels.get('LEVEL_2', {}).get('min', float('inf')): 
                return levels['LEVEL_2']['title']
            if count >= levels.get('LEVEL_1', {}).get('min', float('inf')): 
                return levels['LEVEL_1']['title']
            
            # Se não atingiu nem o Level 1, retorna o DEFAULT (se existir) ou None
            return levels.get('DEFAULT')

        user_ranks['review'] = get_rank_title('REVIEW', self.review_count)
        user_ranks['platinum'] = get_rank_title('PLATINUM', self.platinum_count)
        streak = getattr(self, 'current_streak', 0)
        user_ranks['streak'] = get_rank_title('STREAK', streak)
        
        # Prevenção de quebra para o que ainda vamos construir (Blog, Comments, Votes)
        # O getattr pega o valor se a propriedade existir, senão retorna 0 para não travar a API.
        post_count = getattr(self, 'blog_post_count', 0)
        user_ranks['post'] = get_rank_title('POST', post_count)
        
        comment_count = getattr(self, 'comment_count', 0)
        user_ranks['comment'] = get_rank_title('COMMENT', comment_count)
        
        vote_count = getattr(self, 'vote_count', 0)
        user_ranks['vote'] = get_rank_title('VOTE', vote_count)

        # Retorna apenas os ranks que o usuário efetivamente conquistou (remove os Nones)
        return {k: v for k, v in user_ranks.items() if v is not None}

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