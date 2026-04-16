import uuid
from datetime import datetime, timezone
from sqlalchemy import extract
from app.extensions import db
from app.models import AlbumReview, TrackReview
from app.exceptions import BusinessRuleError, ResourceNotFoundError

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
        is_private = payload.get('is_private', False)
        
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

        artist_id = album_data.get('artist_id') 
        final_genres = []
        if artist_id:
            from app.services.spotify_service import SpotifyService
            final_genres = SpotifyService.get_artist_genres(user, artist_id)

        final_cover_url = album_data.get('cover')
        final_album_id = spotify_id if spotify_id else f"custom:{uuid.uuid4()}"

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
            created_at=final_created_at,
            is_private=is_private,
            artist_genres=final_genres
        )
        
        db.session.add(review)
        db.session.flush()

        ignored_count = 0
        total_tracks = len(tracks_data)

        for track in tracks_data:
            is_ignored = track.get('is_ignored', False)
            score_val = None

            if is_ignored:
                ignored_count += 1
            else:
                try:
                    score_val = float(track['userScore'])
                except (ValueError, KeyError, TypeError):
                    raise BusinessRuleError(f"Nota inválida para a faixa {track.get('name')}.")

            track_review = TrackReview(
                album_review_id=review.id,
                spotify_track_id=track.get('id'),
                track_name=track.get('name'),
                track_number=track.get('track_number'),
                score=score_val,
                is_ignored=is_ignored
            )
            db.session.add(track_review)

        if ignored_count == total_tracks and total_tracks > 0:
            db.session.rollback()
            raise BusinessRuleError("Você não pode ignorar todas as faixas do álbum. Pelo menos uma deve ser avaliada.")

        review.update_stats()
        db.session.commit()

        from app.services.stats_service import StatsService
        StatsService.calculate_and_update_streak(user.id)

        return review

    @staticmethod
    def update_review(user, review_id, payload):
        """
        Atualiza uma review existente (texto e notas das faixas).
        """
        review = AlbumReview.query.filter_by(id=review_id, user_id=user.id).first()
        if not review:
            raise ResourceNotFoundError("Review não encontrada ou você não tem permissão para alterá-la.")

        # Atualiza o texto se foi enviado
        if 'review_text' in payload:
            review.review_text = payload['review_text']

        review.is_private = payload.get('is_private', review.is_private)

        # Atualiza as faixas se foram enviadas
        tracks_data = payload.get('tracks', [])
        if tracks_data:
            ignored_count = 0
            # Pega o total de faixas que já existem no banco para essa review para a validação
            total_tracks = TrackReview.query.filter_by(album_review_id=review.id).count()

            for track_data in tracks_data:
                # Busca a faixa no banco pelo ID do Spotify
                track_review = TrackReview.query.filter_by(
                    album_review_id=review.id, 
                    spotify_track_id=track_data.get('id')
                ).first()

                if track_review:
                    is_ignored = track_data.get('is_ignored', track_review.is_ignored)
                    score_val = None

                    if is_ignored:
                        ignored_count += 1
                    else:
                        try:
                            # Tenta pegar a nota nova, se não vier, mantém a antiga
                            score_val = float(track_data.get('userScore', track_review.score))
                        except (ValueError, TypeError):
                            raise BusinessRuleError(f"Nota nova inválida para a faixa {track_data.get('name')}.")

                    # Aplica as mudanças
                    track_review.is_ignored = is_ignored
                    track_review.score = score_val
                
                # Conta quantas faixas no total acabaram ficando ignoradas
                if not track_review and track_data.get('is_ignored'):
                     ignored_count += 1
            
            # Precisamos contar as faixas que não vieram no payload mas já estavam ignoradas no banco
            already_ignored_in_db = TrackReview.query.filter_by(album_review_id=review.id, is_ignored=True).count()
            # Validação: se todas as faixas do álbum ficarem ignoradas após a edição
            # (Simplificando a checagem: verificamos se sobrou alguma faixa com nota no álbum)
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
        """
        Retorna reviews agrupadas por dia para o calendário.
        """
        reviews = AlbumReview.query.filter(
            AlbumReview.user_id == user_id,
            extract('month', AlbumReview.created_at) == month,
            extract('year', AlbumReview.created_at) == year
        ).order_by(AlbumReview.created_at).all()

        if str(request_user_id) != str(user_id):
            query = query.filter(AlbumReview.is_private == False)
        
        calendar = {}
        for review in reviews:
            day = str(review.created_at.day)
            if day not in calendar:
                calendar[day] = []
            
            calendar[day].append(review)
            
        return calendar

    @staticmethod
    def get_reviews(user_id, page=1, per_page=10, filters=None, request_user_id=None):
        """
        Retorna reviews paginadas para o histórico com filtros opcionais.
        """
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
            
        return pagination