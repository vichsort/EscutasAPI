from flask import Blueprint, request
from app.utils import success_response, require_auth
from app.services import AlbumService, CurationService
from app.exceptions import BusinessRuleError, ResourceNotFoundError
from app.schemas import CurationVoteInput

albums_bp = Blueprint('albums', __name__, url_prefix='/api/albums')

@albums_bp.route('/search', methods=['GET'])
@require_auth
def search_albums(current_user):
    """
    Busca álbuns no Spotify.
    """
    query = request.args.get('q')
    
    if not query:
        raise BusinessRuleError("O termo de busca 'q' é obrigatório.")

    results = AlbumService.search_albums(current_user, query)

    data = [album.model_dump() for album in results]
    
    return success_response(
        data=data, 
        message=f"Encontrados {len(results)} álbuns."
    )

@albums_bp.route('/<spotify_id>', methods=['GET'])
@require_auth
def get_album_details(current_user, spotify_id):
    """
    Retorna os detalhes completos de um álbum.
    """
    album = AlbumService.get_album_details(current_user, spotify_id)

    if not album:
        raise ResourceNotFoundError("Álbum")

    return success_response(
        data=album.model_dump(),
        message="Detalhes do álbum recuperados."
    )

@albums_bp.route('/<spotify_id>/curate', methods=['POST'])
@require_auth
def curate_album(current_user, spotify_id):
    """
    Registra o voto do usuário sobre o status de Platina do álbum.
    Body: {"is_canonical": true/false}
    """
    payload = CurationVoteInput.model_validate(request.json or {})
    
    CurationService.register_vote(
        user_id=current_user.id,
        spotify_album_id=spotify_id,
        is_canonical=payload.is_canonical
    )

    return success_response(
        message="Voto de curadoria registrado. A comunidade agradece!",
        data={"is_canonical": payload.is_canonical}
    )