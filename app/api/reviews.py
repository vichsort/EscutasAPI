from flask import Blueprint, request
from app.utils.response_util import success_response
from app.utils.decorator_util import require_auth
from app.services.review_service import ReviewService
from app.extensions import limiter
from app.models.review import AlbumReview

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')

@reviews_bp.route('', methods=['POST'])
@require_auth
@limiter.limit("5 per minute")
def create_review(current_user):
    """
    Cria uma nova review completa (Álbum + Faixas + Texto).
    
    Payload Esperado (JSON):
    {
        "album": {
            "id": "spotify_album_id",
            "name": "Nome do Album",
            "artist": "Nome do Artista",
            "cover": "url_da_imagem"
        },
        "review_text": "Achei esse álbum incrível porque...",
        "tracks": [
            { "id": "t1", "name": "Faixa 1", "track_number": 1, "userScore": 9.5 },
            { "id": "t2", "name": "Faixa 2", "track_number": 2, "userScore": 8.0 }
        ]
    }
    """
    data = request.json
    result = ReviewService.create_review(current_user, data)

    return success_response(
        data=result,
        message="Review salva com sucesso!",
        status_code=201
    )

@reviews_bp.route('/history', methods=['GET'])
@require_auth
def get_user_history(current_user):
    """
    Retorna todas as reviews do usuário logado, da mais recente para a mais antiga.
    """
    result = ReviewService.get_user_reviews(current_user.id)
        
    return success_response(data=result)

@reviews_bp.route('/<uuid:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Busca uma review específica pelo UUID.
    Útil para compartilhar links: escutas.com/review/uuid-aqui
    """
    review = AlbumReview.query.get_or_404(review_id)
    
    return success_response(data=review.to_dict())