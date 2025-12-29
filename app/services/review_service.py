import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.review import AlbumReview, TrackReview
from app.services.spotify_service import SpotifyService
from app.utils.response_util import APIError

class ReviewService:
    @staticmethod
    def create_review(user, payload):
        """
        Cria uma review de álbum.
        Suporta tanto álbuns do Spotify quanto álbuns manuais (Custom).
        """
        album_data = payload['album']
        tracks_data = payload['tracks']
        review_text = payload.get('review_text')
        spotify_id = album_data.get('id')
        final_album_name = album_data['name']
        final_artist_name = album_data['artist']
        final_cover_url = album_data.get('cover')
        final_album_id = None

        if spotify_id:

            final_album_id = spotify_id
            
            # Opcional: Se for ID do Spotify puro (sem 'custom:'), 
            # podemos buscar metadados atualizados para garantir consistência.
            # Mas se quisermos performance, confiamos no payload.
            # Vamos manter simples: Confiamos no Payload por enquanto.
        else:
            # --- FLUXO MANUAL (Custom) ---
            # Gera um ID único nosso
            final_album_id = f"custom:{uuid.uuid4()}"

        review = AlbumReview(
            user_id=user.id,
            spotify_album_id=final_album_id, # Pode ser '4xWY...' ou 'custom:...'
            album_name=final_album_name,
            artist_name=final_artist_name,
            cover_url=final_cover_url,
            review_text=review_text,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(review)
        db.session.flush() # Gera o ID da review para usar nas tracks

        for track in tracks_data:
            # No fluxo manual, track.get('id') será None.
            # No fluxo Spotify, pode ter ID.
            
            track_review = TrackReview(
                album_review_id=review.id,
                spotify_track_id=track.get('id'),
                track_name=track['name'],
                track_number=track['track_number'],
                score=float(track['userScore'])
            )
            db.session.add(track_review)

        review.update_stats()
        db.session.commit()

        return review

    @staticmethod
    def get_calendar_data(user_id, month, year):
        """
        Retorna reviews agrupadas por dia para o calendário.
        Otimizado para buscar apenas o necessário do banco.
        """
        from sqlalchemy import extract
        
        reviews = AlbumReview.query.filter(
            AlbumReview.user_id == user_id,
            extract('month', AlbumReview.created_at) == month,
            extract('year', AlbumReview.created_at) == year
        ).order_by(AlbumReview.created_at).all()
        
        calendar = {}
        for review in reviews:
            # Agrupa por dia (String "1", "2", "31")
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