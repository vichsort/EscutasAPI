from flask import Blueprint, request
from app.utils.response_util import success_response, paginated_response, error_response
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
    Retorna reviews filtradas e paginadas.
    
    Query Params Suportados:
    - page (int): Padrão 1
    - per_page (int): Padrão 20
    - start_date (YYYY-MM-DD): Filtrar reviews a partir desta data
    - end_date (YYYY-MM-DD): Filtrar reviews até esta data
    - album_id (str): Filtrar reviews de um álbum específico
    """
    # 1. Captura Query Params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'album_id': request.args.get('album_id')
    }
    
    # 2. Chama o Serviço
    pagination = ReviewService.get_reviews(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        filters=filters
    )
    
    # 3. Retorna com Metadados
    return paginated_response(pagination, message="Histórico recuperado com sucesso.")

@reviews_bp.route('/<uuid:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Busca uma review específica pelo UUID.
    Útil para compartilhar links: escutas.com/review/uuid-aqui
    """
    review = AlbumReview.query.get_or_404(review_id)
    
    return success_response(data=review.to_dict())

@reviews_bp.route('/calendar', methods=['GET'])
@require_auth
def get_calendar(current_user):
    """
    Endpoint do Calendário.
    Recebe month (1-12) e year (ex: 2025).
    Retorna dicionário indexado pelo dia.
    """
    try:
        month = int(request.args.get('month'))
        year = int(request.args.get('year'))
        
        if not (1 <= month <= 12):
            return error_response("Mês deve ser entre 1 e 12.", 400)
            
    except (TypeError, ValueError):
        return error_response("Parâmetros 'month' e 'year' são obrigatórios e devem ser números inteiros.", 400)

    # Chama o serviço
    calendar_data = ReviewService.get_calendar_data(current_user.id, month, year)
    
    return success_response(
        data=calendar_data,
        message=f"Dados do calendário de {month}/{year} recuperados."
    )