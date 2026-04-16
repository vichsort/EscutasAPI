from flask import Blueprint, request
from app.utils import success_response, require_auth, paginated_response
from app.models import UserPlatinum
from app.services import UserService, ReviewService, StatsService
from app.schemas import ReviewSummary, PlatinumTrophyOutput, UserStatsOutput
from app.exceptions import BusinessRuleError, ResourceNotFoundError

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/search', methods=['GET'])
@require_auth
def search_users(current_user):
    """
    Busca usuários.
    Uso: GET /api/users/search?q=joao
    """
    query = request.args.get('q')
    
    if not query or len(query) < 2:
        raise BusinessRuleError("Digite pelo menos 2 caracteres para buscar.")
    
    results = UserService.search_users(query)
    data = [user.model_dump() for user in results]
    
    return success_response(
        data=data,
        message=f"Encontrados {len(results)} usuários."
    )

@users_bp.route('/<user_uuid>', methods=['GET'])
@require_auth
def get_profile(current_user, user_uuid):
    """
    Pega dados públicos de um perfil.
    """
    user = UserService.get_user_profile(user_uuid)
    
    if not user:
        raise ResourceNotFoundError("Usuário")
        
    return success_response(data=user.model_dump())

@users_bp.route('/<uuid:target_user_id>/reviews', methods=['GET'])
def get_user_reviews(target_user_id):
    """
    Rota SOCIAL: Permite ver o histórico de reviews de outro usuário.
    """
    target_user = UserService.get_user_profile(str(target_user_id))
    if not target_user:
        raise ResourceNotFoundError("Usuário")

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
        filters=filters,
        request_user_id=None
    )

    items_pydantic = [ReviewSummary.model_validate(item) for item in pagination.items]
    pagination.items = [item.model_dump() for item in items_pydantic]
    
    return paginated_response(
        pagination, 
        message=f"Histórico de {target_user.display_name} recuperado."
    )

@users_bp.route('/<uuid:target_user_id>/calendar', methods=['GET'])
def get_user_calendar(target_user_id):
    """
    Rota SOCIAL: Permite ver o calendário de outro usuário.
    """
    target_user = UserService.get_user_profile(str(target_user_id))
    if not target_user:
        raise ResourceNotFoundError("Usuário")

    try:
        month = int(request.args.get('month'))
        year = int(request.args.get('year'))
        if not (1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        raise BusinessRuleError("Parâmetros 'month' e 'year' inválidos. Use números.")

    calendar_data = ReviewService.get_calendar_data(target_user_id, month, year, request_user_id=None)

    calendar_json = {}
    for day, review_list in calendar_data.items():
        calendar_json[day] = [ReviewSummary.model_validate(r).model_dump() for r in review_list]
    
    return success_response(
        data=calendar_json,
        message=f"Calendário de {target_user.display_name} recuperado."
    )

@users_bp.route('/<uuid:target_user_id>/platinums', methods=['GET'])
def get_user_platinums(target_user_id):
    """Retorna todas as medalhas de platina conquistadas por um usuário."""
    target_user = UserService.get_user_profile(str(target_user_id))
    if not target_user:
        raise ResourceNotFoundError("Usuário")

    trophies = UserPlatinum.query.filter_by(user_id=target_user_id).order_by(UserPlatinum.achieved_at.desc()).all()
    
    data = [PlatinumTrophyOutput.model_validate(t).model_dump() for t in trophies]
    
    return success_response(
        data=data,
        message=f"{target_user.display_name} possui {len(data)} platinas."
    )

@users_bp.route('/<uuid:target_user_id>/stats', methods=['GET'])
def get_user_stats(target_user_id):
    """Retorna as estatísticas do perfil público de um usuário."""
    target_user = UserService.get_user_profile(str(target_user_id))
    if not target_user:
        raise ResourceNotFoundError("Usuário")

    raw_stats = StatsService.get_user_stats(target_user_id)
    data = UserStatsOutput.model_validate(raw_stats).model_dump()
    
    return success_response(
        data=data,
        message=f"Estatísticas de {target_user.display_name} calculadas."
    )