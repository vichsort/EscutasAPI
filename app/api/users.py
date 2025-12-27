from flask import Blueprint, request
from app.utils.response_util import success_response, error_response
from app.utils.decorator_util import require_auth
from app.services.user_service import UserService

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
        return error_response("Digite pelo menos 2 caracteres para buscar.", 400)
    
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
        return error_response("Usuário não encontrado.", 404)
        
    return success_response(data=user.model_dump())