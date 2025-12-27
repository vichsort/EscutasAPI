import bleach
from typing import List, Dict
from datetime import datetime
from sqlalchemy import extract, and_
from app.extensions import db
from app.models.review import AlbumReview, TrackReview
from app.models.user import User
from app.utils.response_util import APIError
from sqlalchemy.orm import joinedload

from app.schemas.review import ReviewSummary, ReviewFull

class ReviewService:
    
    @staticmethod
    def create_review(user: User, data: dict) -> ReviewFull:
        """
        Cria uma review e retorna o objeto Pydantic ReviewFull.
        """
        # 1. Validação de Dados (Sanitization)
        raw_text = data.get('review_text', '')
        clean_text = bleach.clean(raw_text, tags=[], strip=True)

        if len(clean_text) > 5000:
            raise APIError("Texto muito longo. Máximo 5000 caracteres.", 400)

        album_data = data.get('album')
        tracks_data = data.get('tracks', [])

        if not album_data or not tracks_data:
            raise APIError("Dados do álbum ou faixas estão faltando.", 400)

        # 2. Lógica de Persistência
        try:
            review = AlbumReview(
                user_id=user.id,
                spotify_album_id=album_data['id'],
                album_name=album_data['name'],
                artist_name=album_data['artist'],
                cover_url=album_data['cover'],
                review_text=clean_text
            )

            for t_data in tracks_data:
                # Validação extra de nota
                try:
                    score = float(t_data['userScore'])
                except (ValueError, TypeError):
                     raise APIError(f"Nota inválida na faixa {t_data.get('name')}", 400)

                if not (0 <= score <= 10):
                    raise APIError(f"Nota inválida na faixa {t_data.get('name')}", 400)

                track = TrackReview(
                    spotify_track_id=t_data['id'],
                    track_name=t_data['name'],
                    track_number=t_data['track_number'],
                    score=score
                )
                review.tracks.append(track)

            review.update_stats()
            
            db.session.add(review)
            db.session.commit()

            return ReviewFull.model_validate(review)

        except APIError:
            raise
        except Exception as e:
            db.session.rollback()
            print(f"Erro no banco: {e}") 
            raise APIError("Falha ao salvar review no banco de dados.", 500)

    @staticmethod
    def get_reviews(user_id, page=1, per_page=20, filters=None):
        """
        Busca reviews com filtros dinâmicos e paginação.
        Retorna o objeto Pagination do SQLAlchemy (o Controller serializa os itens).
        """
        query = AlbumReview.query.options(joinedload(AlbumReview.tracks)).filter_by(user_id=user_id)
        
        if filters:
            if filters.get('album_id'):
                query = query.filter_by(spotify_album_id=filters['album_id'])
            
            if filters.get('start_date'):
                try:
                    dt_start = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                    query = query.filter(AlbumReview.created_at >= dt_start)
                except ValueError:
                    pass

            if filters.get('end_date'):
                try:
                    dt_end = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                    query = query.filter(AlbumReview.created_at <= dt_end)
                except ValueError:
                    pass

        query = query.order_by(AlbumReview.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_calendar_data(user_id, month, year) -> Dict[str, List[ReviewSummary]]:
        """
        Retorna as reviews organizadas por dia para o calendário.
        Retorna um dicionário onde os valores são Listas de ReviewSummary (Pydantic).
        """
        reviews = AlbumReview.query.filter(
            and_(
                AlbumReview.user_id == user_id,
                extract('month', AlbumReview.created_at) == month,
                extract('year', AlbumReview.created_at) == year
            )
        ).order_by(AlbumReview.created_at.desc()).all()
        
        calendar_map = {}
        
        for review in reviews:
            day = str(review.created_at.day)
            
            if day not in calendar_map:
                calendar_map[day] = []

            summary = ReviewSummary.model_validate(review)
            calendar_map[day].append(summary)
                
        return calendar_map