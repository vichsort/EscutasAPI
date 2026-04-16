from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc
from app.extensions import db
from app.models import AlbumReview, User
from app.constants import HALL_OF_FAME_MIN_REVIEWS, TRENDING_DAYS_LIMIT
from app.schemas import ReviewSummary

class ExploreService:

    @staticmethod
    def get_trending_albums(limit=10) -> list:
        """
        Retorna os álbuns com mais reviews públicas nos últimos X dias.
        """
        days_ago = datetime.now(timezone.utc) - timedelta(days=TRENDING_DAYS_LIMIT)

        trending_query = db.session.query(
            AlbumReview.spotify_album_id,
            AlbumReview.album_name,
            AlbumReview.artist_name,
            AlbumReview.cover_url,
            func.count(AlbumReview.id).label('review_count'),
            func.avg(AlbumReview.score).label('average_score')
        ).filter(
            AlbumReview.is_private == False,
            AlbumReview.created_at >= days_ago
        ).group_by(
            AlbumReview.spotify_album_id,
            AlbumReview.album_name,
            AlbumReview.artist_name,
            AlbumReview.cover_url
        ).order_by(desc('review_count')).limit(limit).all()

        return [
            {
                "album_id": row.spotify_album_id,
                "name": row.album_name,
                "artist": row.artist_name,
                "cover_url": row.cover_url,
                "review_count": row.review_count,
                "average_score": round(row.average_score, 2) if row.average_score else 0.0
            } for row in trending_query
        ]

    @staticmethod
    def get_hall_of_fame(limit=10) -> list:
        """
        Retorna os álbuns com a maior média de notas de todos os tempos.
        Exige um número mínimo de reviews para evitar que um álbum com 1 review nota 10 ganhe.
        """
        fame_query = db.session.query(
            AlbumReview.spotify_album_id,
            AlbumReview.album_name,
            AlbumReview.artist_name,
            AlbumReview.cover_url,
            func.count(AlbumReview.id).label('review_count'),
            func.avg(AlbumReview.score).label('average_score')
        ).filter(
            AlbumReview.is_private == False
        ).group_by(
            AlbumReview.spotify_album_id,
            AlbumReview.album_name,
            AlbumReview.artist_name,
            AlbumReview.cover_url
        ).having(
            func.count(AlbumReview.id) >= HALL_OF_FAME_MIN_REVIEWS
        ).order_by(desc('average_score'), desc('review_count')).limit(limit).all()

        return [
            {
                "album_id": row.spotify_album_id,
                "name": row.album_name,
                "artist": row.artist_name,
                "cover_url": row.cover_url,
                "review_count": row.review_count,
                "average_score": round(row.average_score, 2) if row.average_score else 0.0
            } for row in fame_query
        ]

    @staticmethod
    def get_global_feed(limit=20) -> list:
        """
        Retorna as reviews públicas mais recentes feitas por qualquer usuário na plataforma.
        """
        reviews = AlbumReview.query.filter_by(is_private=False)\
            .order_by(AlbumReview.created_at.desc())\
            .limit(limit).all()
        
        return [ReviewSummary.model_validate(r).model_dump() for r in reviews]

    @staticmethod
    def get_top_reviewers(limit=5) -> list:
        """
        Retorna os usuários que mais fizeram reviews públicas nos últimos X dias.
        """
        days_ago = datetime.now(timezone.utc) - timedelta(days=TRENDING_DAYS_LIMIT)

        top_users_query = db.session.query(
            User.id,
            User.display_name,
            User.avatar_url,
            func.count(AlbumReview.id).label('review_count')
        ).join(
            AlbumReview, User.id == AlbumReview.user_id
        ).filter(
            AlbumReview.is_private == False,
            AlbumReview.created_at >= days_ago
        ).group_by(
            User.id,
            User.display_name,
            User.avatar_url
        ).order_by(desc('review_count')).limit(limit).all()

        return [
            {
                "user_id": str(row.id),
                "display_name": row.display_name,
                "avatar_url": row.avatar_url,
                "review_count": row.review_count
            } for row in top_users_query
        ]