import bleach
from app.extensions import db
from app.models.review import AlbumReview, TrackReview
from app.models.user import User
from app.utils.response_util import APIError

class ReviewService:
    
    @staticmethod
    def create_review(user: User, data: dict) -> dict:
        """
        Contém TODA a regra de negócio para criar uma review.
        Lança APIError se algo estiver errado.
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
                score = float(t_data['userScore'])
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
            
            return review.to_dict()

        except APIError:
            raise # Repassa erros que nós mesmos criamos
        except Exception as e:
            db.session.rollback()
            # Logar o erro real aqui seria o ideal
            print(f"Erro no banco: {e}") 
            raise APIError("Falha ao salvar review no banco de dados.", 500)

    @staticmethod
    def get_user_reviews(user_id):
        reviews = AlbumReview.query.filter_by(user_id=user_id)\
            .order_by(AlbumReview.created_at.desc())\
            .all()
        return [r.to_dict() for r in reviews]