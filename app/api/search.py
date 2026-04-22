from flask import Blueprint, request
from app.services import SearchService
from app.utils import success_response, require_auth

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('', methods=['GET'])
@require_auth
def quick_search(current_user):
    """
    Busca rápida e achatada para dropdowns e autocomplete (@).
    Ex: GET /api/search?q=daft+punk&limit=3
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 3, type=int)

    # não busca se for só 1 letra (poupa processamento)
    if len(query) < 2:
        return success_response(data=[])

    results = SearchService.quick_search(query=query, limit_per_type=limit)

    # converte a lista de schemas Pydantic para um formato JSON amigável
    data = [item.model_dump(mode='json') for item in results]

    return success_response(
        data=data,
        message="Busca rápida concluída."
    )