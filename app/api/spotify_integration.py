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
    Se não estiver a ouvir nada ou for podcast, retorna null no campo 'data'.
    """
    result = SpotifyService.get_currently_playing(current_user)

    return success_response(data=result, message="Status do player recuperado.")

@spotify_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_suggestions(current_user):
    """
    Retorna álbuns sugeridos baseados no histórico recente.
    Aplica a regra de ouro: só sugere se ouviu >= 3 músicas do álbum.
    """
    suggestions = SpotifyService.get_recently_played_suggestions(current_user)
    
    return success_response(
        data=suggestions, 
        message=f"Encontradas {len(suggestions)} sugestões de álbuns."
    )