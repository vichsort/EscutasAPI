from flask import Blueprint, request
from app.utils import success_response, paginated_response, require_auth
from app.services.review_service import ReviewService, SpotifyService
from app.schemas import ReviewSummary
from app.exceptions import BusinessRuleError

me_bp = Blueprint('me', __name__, url_prefix='/api/me')

@me_bp.route('', methods=['GET'])
@require_auth
def get_my_profile(current_user):
    """
    Retorna os dados do próprio usuário logado.
    """
    return success_response(
        data=current_user.to_dict(),
        message="Perfil recuperado com sucesso."
    )

@me_bp.route('/reviews', methods=['GET'])
@require_auth
def get_my_reviews(current_user):
    """
    Retorna o histórico de reviews do usuário logado (paginado e filtrado).
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'album_id': request.args.get('album_id'),
        'tier': request.args.get('tier'),
        'search': request.args.get('search')
    }
    
    pagination = ReviewService.get_reviews(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        filters=filters
    )

    items_pydantic = [ReviewSummary.model_validate(item) for item in pagination.items]
    pagination.items = [item.model_dump() for item in items_pydantic]
    
    return paginated_response(pagination, message="Seu histórico recuperado com sucesso.")

@me_bp.route('/calendar', methods=['GET'])
@require_auth
def get_my_calendar(current_user):
    """
    Retorna dados do calendário do usuário logado.
    """
    try:
        month = int(request.args.get('month'))
        year = int(request.args.get('year'))
        if not (1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        raise BusinessRuleError("Parâmetros 'month' e 'year' inválidos. Use números.")

    calendar_data = ReviewService.get_calendar_data(current_user.id, month, year)

    calendar_json = {}
    for day, review_list in calendar_data.items():
        calendar_json[day] = [ReviewSummary.model_validate(r).model_dump() for r in review_list]
    
    return success_response(
        data=calendar_json,
        message=f"Seu calendário de {month}/{year} recuperado."
    )

@me_bp.route('/now-playing', methods=['GET'])
@require_auth
def get_now_playing(current_user):
    """
    Retorna o que o usuário está ouvindo agora no Spotify.
    """
    track_data = SpotifyService.get_now_playing(current_user)
    
    return success_response(
        data=track_data,
        message="Buscando a música atual." if track_data else "Nada tocando no momento."
    )

@me_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_suggestions(current_user):
    """
    Retorna recomendações personalizadas do Spotify para o usuário.
    """
    suggestions = SpotifyService.get_suggestions(current_user)
    
    return success_response(
        data=suggestions,
        message="Sugestões recuperadas."
    )