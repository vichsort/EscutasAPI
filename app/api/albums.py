from flask import Blueprint, request
from app.utils.response_util import success_response, error_response
from app.utils.decorator_util import require_auth
from app.services.album_service import AlbumService

albums_bp = Blueprint('albums', __name__, url_prefix='/api/albums')

@albums_bp.route('/search', methods=['GET'])
@require_auth
def search_albums(current_user):
    """
    Busca álbuns no Spotify.
    """
    query = request.args.get('q')
    
    if not query:
        return error_response("O termo de busca 'q' é obrigatório.", 400)

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
        return error_response("Álbum não encontrado ou erro no Spotify.", 404)

    return success_response(
        data=album.model_dump(),
        message="Detalhes do álbum recuperados."
    )