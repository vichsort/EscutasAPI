import uuid
from app.schemas import ReviewSummary
from app.extensions import db
from app.models import AlbumReview, TrackReview
from app.exceptions import BusinessRuleError, ResourceNotFoundError

class ReviewService:
    @staticmethod
    def create_review(user, payload):
        """Cria uma review de álbum (Os dados já chegaram mastigados e validados pelo Pydantic!)."""
        album_data = payload.get('album', {})
        tracks_data = payload.get('tracks', [])
        
        # Pydantic já transformou isso num objeto datetime UTC!
        final_created_at = payload.get('listened_date') 

        spotify_id = album_data.get('id')
        final_album_name = album_data.get('name')
        final_artist_name = album_data.get('artist')
        final_cover_url = album_data.get('cover')
        
        # Código duplicado resolvido com um ternário elegante
        final_album_id = spotify_id if spotify_id else f"custom:{uuid.uuid4()}"

        # Busca gêneros
        artist_id = album_data.get('artist_id') 
        final_genres = []
        if artist_id:
            from app.services.spotify_service import SpotifyService
            final_genres = SpotifyService.get_artist_genres(user, artist_id)

        # Criando o registro pai
        review = AlbumReview(
            user_id=user.id,
            spotify_album_id=final_album_id,
            album_name=final_album_name,
            artist_name=final_artist_name,
            cover_url=final_cover_url,
            review_text=payload.get('review_text'),
            created_at=final_created_at,
            is_private=payload.get('is_private', False),
            artist_genres=final_genres
        )
        
        db.session.add(review)
        db.session.flush()

        # O Pydantic já validou que as notas são floats válidos e que pelo menos 1 faixa foi avaliada!
        for track in tracks_data:
            track_review = TrackReview(
                album_review_id=review.id,
                spotify_track_id=track.get('id'),
                track_name=track.get('name'),
                track_number=track.get('track_number'),
                score=track.get('userScore'), # Se for ignorada, será None automaticamente
                is_ignored=track.get('is_ignored', False)
            )
            db.session.add(track_review)

        review.update_stats()
        db.session.commit()

        from app.services.stats_service import StatsService
        StatsService.calculate_and_update_streak(user.id)

        return review

    staticmethod
    def update_review(user, review_id, payload):
        """
        Atualiza uma review existente.
        Espera-se que o 'payload' já tenha sido validado por um schema (ex: ReviewUpdate).
        """
        review = AlbumReview.query.filter_by(id=review_id, user_id=user.id).first()
        if not review:
            raise ResourceNotFoundError("Review não encontrada ou você não tem permissão para alterá-la.")

        # Atualiza campos básicos
        if 'review_text' in payload:
            review.review_text = payload['review_text']
            
        if 'is_private' in payload:
            review.is_private = payload['is_private']

        # Atualiza as faixas se foram enviadas
        tracks_data = payload.get('tracks', [])
        if tracks_data:
            for track_data in tracks_data:
                # Busca a faixa no banco pelo ID do Spotify
                track_review = TrackReview.query.filter_by(
                    album_review_id=review.id, 
                    spotify_track_id=track_data.get('id')
                ).first()

                if track_review:
                    # Como o Pydantic já validou, podemos confiar cegamente nos dados
                    track_review.is_ignored = track_data.get('is_ignored', track_review.is_ignored)
                    
                    # O dict.get retorna None se a chave não existir, mantendo a nota antiga se o usuário não enviou
                    if not track_review.is_ignored:
                        track_review.score = track_data.get('userScore', track_review.score)
                    else:
                        track_review.score = None # Se ignorou agora, a nota evapora

            # PREPARA AS MUDANÇAS NA MEMÓRIA DO BANCO ANTES DE PERGUNTAR
            db.session.flush()

            # Sobrou alguma faixa avaliada no álbum inteiro? (nothing pro beta)
            has_valid_track = TrackReview.query.filter_by(album_review_id=review.id, is_ignored=False).first()
            
            if not has_valid_track:
                db.session.rollback()
                raise BusinessRuleError("Você não pode ignorar todas as faixas do álbum. Pelo menos uma deve ser avaliada.")

            # Recalcula a nota média e o tier do álbum baseado nas novas notas
            review.update_stats()

        db.session.commit()
        return review

    @staticmethod
    def delete_review(user, review_id):
        """
        Deleta uma review do usuário e recalcula as estatísticas.
        """
        review = AlbumReview.query.filter_by(id=review_id, user_id=user.id).first()
        if not review:
            raise ResourceNotFoundError("Review não encontrada ou você não tem permissão para apagá-la.")

        db.session.delete(review)
        db.session.commit()

        from app.services.stats_service import StatsService
        StatsService.calculate_and_update_streak(user.id)

        return True

    @staticmethod
    def get_calendar_data(user_id, month, year, request_user_id=None):
        """Retorna reviews agrupadas por dia para o calendário (Já formatadas para JSON)."""
        from sqlalchemy import extract
        
        # Constrói a Base da Busca
        query = AlbumReview.query.filter(
            AlbumReview.user_id == user_id,
            extract('month', AlbumReview.created_at) == month,
            extract('year', AlbumReview.created_at) == year
        )

        # Aplica o Filtro de Privacidade se for um visitante
        if str(request_user_id) != str(user_id):
            query = query.filter(AlbumReview.is_private == False)
        
        # Executa a busca
        reviews = query.order_by(AlbumReview.created_at).all()
        
        calendar = {}
        for review in reviews:
            day = str(review.created_at.day)
            if day not in calendar:
                calendar[day] = []
            
            calendar[day].append(ReviewSummary.model_validate(review).model_dump())
            
        return calendar

    @staticmethod
    def get_reviews(user_id, page=1, per_page=10, filters=None, request_user_id=None):
        """Retorna reviews paginadas para o histórico com filtros opcionais (Já formatadas)."""
        query = AlbumReview.query.filter_by(user_id=user_id)

        if str(request_user_id) != str(user_id):
            query = query.filter_by(is_private=False)
        
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
            
        items_pydantic = [ReviewSummary.model_validate(item) for item in pagination.items]
        pagination.items = [item.model_dump() for item in items_pydantic]
            
        return pagination