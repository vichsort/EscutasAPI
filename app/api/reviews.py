from flask import Blueprint, request
from app.utils.response_util import success_response, paginated_response, error_response
from app.utils.decorator_util import require_auth
from app.services.review_service import ReviewService
from app.services.user_service import UserService
from app.extensions import limiter
from app.models.review import AlbumReview
from app.schemas.review import ReviewFull, ReviewSummary, ReviewCreate

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')

@reviews_bp.route('', methods=['POST'])
@require_auth
@limiter.limit("5 per minute")
def create_review(current_user):
    """
    Cria uma nova review completa.
    Retorna o objeto validado pelo Schema ReviewFull.
    """
    payload_validado = ReviewCreate(**request.json)

    result_orm = ReviewService.create_review(current_user, payload_validado.model_dump())

    return success_response(
        data=ReviewFull.model_validate(result_orm).model_dump(),
        message="Review salva com sucesso!",
        status_code=201
    )

@reviews_bp.route('/history', methods=['GET'])
@require_auth
def get_user_history(current_user):
    """
    Retorna reviews filtradas.
    Aqui aplicamos o Schema ReviewSummary em cada item da paginação.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'album_id': request.args.get('album_id')
    }
    
    pagination = ReviewService.get_reviews(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        filters=filters
    )
    
    items_pydantic = [ReviewSummary.model_validate(item) for item in pagination.items]
    items_dict = [item.model_dump() for item in items_pydantic]

    pagination.items = items_dict 
    
    return paginated_response(pagination, message="Histórico recuperado com sucesso.")

@reviews_bp.route('/<uuid:review_id>', methods=['GET'])
def get_review_details(review_id):
    """
    Busca review pelo UUID.
    Usa ReviewFull para garantir formato consistente com o create.
    """
    review = AlbumReview.query.get_or_404(review_id)
    
    return success_response(
        data=ReviewFull.model_validate(review).model_dump()
    )

@reviews_bp.route('/calendar', methods=['GET'])
@require_auth
def get_calendar(current_user):
    """
    Retorna dados do calendário.
    """
    try:
        month = int(request.args.get('month'))
        year = int(request.args.get('year'))
        if not (1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        return error_response("Parâmetros 'month' e 'year' inválidos.", 400)

    calendar_data = ReviewService.get_calendar_data(current_user.id, month, year)

    calendar_json = {}
    for day, review_list in calendar_data.items():
        calendar_json[day] = [r.model_dump() for r in review_list]
    
    return success_response(
        data=calendar_json,
        message=f"Dados do calendário de {month}/{year} recuperados."
    )

    
@reviews_bp.route('/user/<uuid:target_user_id>/history', methods=['GET'])
@require_auth
def get_social_history(current_user, target_user_id):
    """
    Rota SOCIAL: Permite ver a lista de reviews (histórico) de outro usuário.
    Suporta os mesmos filtros da rota pessoal (paginação, datas, álbum).
    """
    target_user = UserService.get_user_profile(str(target_user_id))
    if not target_user:
        return error_response("Usuário não encontrado.", 404)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'album_id': request.args.get('album_id')
    }
    
    pagination = ReviewService.get_reviews(
        user_id=target_user_id,
        page=page,
        per_page=per_page,
        filters=filters
    )

    items_pydantic = [ReviewSummary.model_validate(item) for item in pagination.items]
    items_dict = [item.model_dump() for item in items_pydantic]
    
    pagination.items = items_dict 
    
    return paginated_response(
        pagination, 
        message=f"Histórico de {target_user.display_name} recuperado."
    )

@reviews_bp.route('/user/<uuid:target_user_id>/calendar', methods=['GET'])
@require_auth
def get_user_calendar(current_user, target_user_id):
    """
    Rota SOCIAL: Permite ver o calendário de outro usuário.
    URL: /api/reviews/user/<uuid>/calendar?month=12&year=2025
    """
    target_user = UserService.get_user_profile(str(target_user_id))
    if not target_user:
        return error_response("Usuário não encontrado.", 404)

    try:
        month = int(request.args.get('month'))
        year = int(request.args.get('year'))
        if not (1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        return error_response("Parâmetros 'month' e 'year' inválidos.", 400)

    calendar_data = ReviewService.get_calendar_data(target_user_id, month, year)

    calendar_json = {}
    for day, review_list in calendar_data.items():
        calendar_json[day] = [r.model_dump() for r in review_list]
    
    return success_response(
        data=calendar_json,
        message=f"Calendário de {target_user.display_name} recuperado."
    )