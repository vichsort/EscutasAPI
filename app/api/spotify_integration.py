from flask import Blueprint
from app.utils.response_util import success_response
from app.utils.decorator_util import require_auth
from app.services.spotify_service import SpotifyService

spotify_bp = Blueprint('spotify', __name__, url_prefix='/api/spotify')

@spotify_bp.route('/now-playing', methods=['GET'])
@require_auth
def get_now_playing(current_user):
    """
    Retorna o que o usuário está a ouvir no momento.
    """
    result_obj = SpotifyService.get_currently_playing(current_user)

    data = result_obj.model_dump() if result_obj else None

    return success_response(
        data=data, 
        message="Status do player recuperado."
    )

@spotify_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_suggestions(current_user):
    """
    Retorna álbuns sugeridos baseados no histórico recente.
    """
    suggestions_list = SpotifyService.get_recently_played_suggestions(current_user)

    data = [item.model_dump() for item in suggestions_list]
    
    return success_response(
        data=data, 
        message=f"Encontradas {len(data)} sugestões de álbuns."
    )