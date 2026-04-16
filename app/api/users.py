from flask import Blueprint, request
from pydantic import ValidationError
from app.utils import success_response, require_auth, paginated_response, resolve_target_user 
from app.models import UserPlatinum
from app.services import UserService, ReviewService, StatsService, MetaService
from app.schemas import PlatinumTrophyOutput, UserStatsOutput
from app.schemas.review import CalendarQuery, ReviewHistoryQuery
from app.exceptions import BusinessRuleError, ResourceNotFoundError

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/search', methods=['GET'])
@require_auth
def search_users(current_user):
    """Busca usuários por nome ou ID do Spotify."""
    query = request.args.get('q')
    
    if not query or len(query) < 2:
        raise BusinessRuleError("Digite pelo menos 2 caracteres para buscar.")
    
    results = UserService.search_users(query)
    data = [user.model_dump() for user in results]
    
    return success_response(
        data=data,
        message=f"Encontrados {len(results)} usuários."
    )

@users_bp.route('/<string:user_param>', methods=['GET'])
@require_auth
def get_profile(current_user, user_param):
    """Pega dados públicos de um perfil ou do próprio usuário ('me')."""
    target_id, _ = resolve_target_user(user_param, current_user)
    
    user = UserService.get_user_profile(target_id)
    if not user:
        raise ResourceNotFoundError("Usuário")
        
    return success_response(data=user.model_dump())

@users_bp.route('/<string:user_param>/reviews', methods=['GET'])
@require_auth
def get_user_reviews(current_user, user_param):
    """Histórico de reviews (Paginação e Filtros)."""
    target_id, req_user_id = resolve_target_user(user_param, current_user)

    # O Pydantic engole o request.args e valida tudo! Adeus try/except.
    try:
        query_data = ReviewHistoryQuery.model_validate(request.args.to_dict())
    except ValidationError as e:
        raise BusinessRuleError(f"Parâmetros de busca inválidos.")

    # Passamos os filtros limpinhos pro Service
    pagination = ReviewService.get_reviews(
        user_id=target_id,
        page=query_data.page,
        per_page=query_data.per_page,
        filters=query_data.model_dump(exclude={'page', 'per_page'}, exclude_none=True),
        request_user_id=req_user_id
    )
    
    # O Service já formatou os itens, o Controller só entrega!
    return paginated_response(pagination, message="Histórico recuperado com sucesso.")

@users_bp.route('/<string:user_param>/calendar', methods=['GET'])
@require_auth
def get_user_calendar(current_user, user_param):
    """Retorna o calendário de reviews."""
    target_id, req_user_id = resolve_target_user(user_param, current_user)

    try:
        query_data = CalendarQuery.model_validate(request.args.to_dict())
    except ValidationError:
        raise BusinessRuleError("Parâmetros 'month' e 'year' são obrigatórios e devem ser válidos.")

    # O Service devolve o JSON perfeitamente montado
    calendar_json = ReviewService.get_calendar_data(
        user_id=target_id, 
        month=query_data.month, 
        year=query_data.year, 
        request_user_id=req_user_id
    )
    
    return success_response(data=calendar_json)

@users_bp.route('/<string:user_param>/platinums', methods=['GET'])
@require_auth
def get_user_platinums(current_user, user_param):
    """Retorna as medalhas de platina do usuário."""
    target_id, _ = resolve_target_user(user_param, current_user)

    trophies = UserPlatinum.query.filter_by(user_id=target_id).order_by(UserPlatinum.achieved_at.desc()).all()
    data = [PlatinumTrophyOutput.model_validate(t).model_dump() for t in trophies]
    
    return success_response(
        data=data,
        message=f"Foram encontradas {len(data)} platinas."
    )

@users_bp.route('/<string:user_param>/stats', methods=['GET'])
@require_auth
def get_user_stats(current_user, user_param):
    """Retorna as estatísticas para os gráficos de perfil."""
    target_id, req_user_id = resolve_target_user(user_param, current_user)

    raw_stats = StatsService.get_user_stats(target_id, request_user_id=req_user_id)
    data = UserStatsOutput.model_validate(raw_stats).model_dump()
    
    return success_response(data=data, message="Estatísticas calculadas com sucesso.")

@users_bp.route('/<string:user_param>/monthly-title', methods=['GET'])
@require_auth
def get_monthly_title(current_user, user_param):
    """Busca o título do mês do usuário."""
    target_id, _ = resolve_target_user(user_param, current_user)

    try:
        query_data = CalendarQuery.model_validate(request.args.to_dict())
    except ValidationError:
        raise BusinessRuleError("Parâmetros 'month' e 'year' são inválidos.")

    title = MetaService.get_monthly_title(target_id, query_data.month, query_data.year)
    
    return success_response(
        data={"month": query_data.month, "year": query_data.year, "title": title},
        message="Título recuperado." if title else "Nenhum título para este mês."
    )