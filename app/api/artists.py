from flask import Blueprint
from app.utils import success_response, require_auth
from app.services import ArtistService
from app.schemas import PlatinumProgressOutput

artists_bp = Blueprint('artists', __name__, url_prefix='/api/artists')

@artists_bp.route('/<artist_id>/progress', methods=['GET'])
@require_auth
def get_platinum_progress(current_user, artist_id):
    """
    Calcula e retorna o progresso de Platina para o artista informado.
    Uso: GET /api/artists/4xWY.../progress
    """
    progress_data = ArtistService.get_platinum_progress(current_user, artist_id)
    data = PlatinumProgressOutput.model_validate(progress_data).model_dump()
    
    return success_response(
        data=data,
        message=f"Progresso da platina de {data['artist']['name']} calculado com sucesso."
    )