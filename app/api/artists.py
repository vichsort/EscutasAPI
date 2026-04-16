from flask import Blueprint, request
from app.utils import success_response, require_auth
from app.services import ArtistService
from app.schemas import PlatinumProgressOutput
from app.exceptions import BusinessRuleError

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

@artists_bp.route('/search', methods=['GET'])
def search_artists():
    """
    Busca de Artistas (Pública).
    O Frontend pode chamar esta rota em paralelo com a busca de álbuns 
    para montar uma 'Busca Unificada'.
    """
    query = request.args.get('q')
    
    if not query or len(query) < 2:
        raise BusinessRuleError("Digite pelo menos 2 caracteres para buscar.")

    # Passamos user=None pois a busca de catálogo é pública e rápida
    artists = ArtistService.search_artists(user=None, query=query)
    
    return success_response(
        data=artists, 
        message=f"Encontrados {len(artists)} artistas."
    )

@artists_bp.route('/<string:artist_id>/discography', methods=['GET'])
@require_auth
def get_artist_discography(current_user, artist_id):
    """
    A 'Página do Artista'.
    Reaproveita o Motor de Platina para devolver a discografia limpa, 
    agrupada e já informando quais álbuns o usuário logado já avaliou!
    """
    if not artist_id:
        raise BusinessRuleError("ID do artista é obrigatório.")

    # O nosso motor pesado já faz tudo isso!
    data = ArtistService.get_platinum_progress(current_user, artist_id)
    
    return success_response(
        data=data, 
        message="Discografia recuperada com sucesso."
    )