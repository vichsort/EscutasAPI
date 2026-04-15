import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.review import AlbumReview, TrackReview
from app.services.spotify_service import SpotifyService

# Trazendo nosso tratamento de erro chique
from app.exceptions import BusinessRuleError

class ReviewService:
    @staticmethod
    def create_review(user, payload):
        """
        Cria uma review de álbum.
        """
        album_data = payload.get('album', {})
        tracks_data = payload.get('tracks', [])
        review_text = payload.get('review_text')
        listened_date_str = payload.get('listened_date')
        
        if listened_date_str:
            try:
                # Converte dd/mm/yyyy para datetime
                parsed_date = datetime.strptime(listened_date_str, "%d/%m/%Y")
                final_created_at = parsed_date.replace(tzinfo=timezone.utc)
            except ValueError:
                raise BusinessRuleError("Formato de data inválido. Use dd/mm/yyyy.")
        else:
            final_created_at = datetime.now(timezone.utc)


        spotify_id = album_data.get('id')
        final_album_name = album_data.get('name')
        final_artist_name = album_data.get('artist')
        final_cover_url = album_data.get('cover')
        final_album_id = None

        if spotify_id:
            final_album_id = spotify_id
        else:
            final_album_id = f"custom:{uuid.uuid4()}"

        # Criando o registro pai
        review = AlbumReview(
            user_id=user.id,
            spotify_album_id=final_album_id,
            album_name=final_album_name,
            artist_name=final_artist_name,
            cover_url=final_cover_url,
            review_text=review_text,
            created_at=final_created_at
        )
        
        db.session.add(review)
        db.session.flush()

        for track in tracks_data:
            try:
                score_val = float(track['userScore'])
            except (ValueError, KeyError):
                raise BusinessRuleError(f"Nota inválida para a faixa {track.get('name')}.")

            track_review = TrackReview(
                album_review_id=review.id,
                spotify_track_id=track.get('id'),
                track_name=track.get('name'),
                track_number=track.get('track_number'),
                score=score_val
            )
            db.session.add(track_review)

        review.update_stats()
        db.session.commit()

        return review

    @staticmethod
    def get_calendar_data(user_id, month, year):
        """
        Retorna reviews agrupadas por dia para o calendário.
        """
        from sqlalchemy import extract
        
        reviews = AlbumReview.query.filter(
            AlbumReview.user_id == user_id,
            extract('month', AlbumReview.created_at) == month,
            extract('year', AlbumReview.created_at) == year
        ).order_by(AlbumReview.created_at).all()
        
        calendar = {}
        for review in reviews:
            day = str(review.created_at.day)
            if day not in calendar:
                calendar[day] = []
            
            calendar[day].append(review)
            
        return calendar

    @staticmethod
    def get_reviews(user_id, page=1, per_page=10, filters=None):
        """
        Retorna reviews paginadas para o histórico com filtros opcionais.
        """
        query = AlbumReview.query.filter_by(user_id=user_id)
        
        if filters:
            if filters.get('tier'):
                query = query.filter(AlbumReview.tier == filters['tier'])
            if filters.get('search'):
                term = f"%{filters['search']}%"
                query = query.filter(
                    (AlbumReview.album_name.ilike(term)) | 
                    (AlbumReview.artist_name.ilike(term))
                )

        pagination = query.order_by(AlbumReview.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
            
        return pagination