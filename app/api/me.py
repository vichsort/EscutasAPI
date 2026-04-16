from flask import Blueprint, request
from app.utils import success_response, require_auth
from app.services import SpotifyService, MetaService
from app.exceptions import BusinessRuleError

me_bp = Blueprint('me', __name__, url_prefix='/api/me')

@me_bp.route('', methods=['GET'])
@require_auth
def get_my_profile(current_user):
    """
    Retorna os dados do próprio usuário logado.
    """
    return success_response(
        data=current_user.to_dict(),
        message="Perfil recuperado com sucesso."
    )

@me_bp.route('/now-playing', methods=['GET'])
@require_auth
def get_now_playing(current_user):
    """
    Retorna o que o usuário está ouvindo agora no Spotify.
    """
    track_data = SpotifyService.get_now_playing(current_user)
    
    return success_response(
        data=track_data,
        message="Buscando a música atual." if track_data else "Nada tocando no momento."
    )

@me_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_suggestions(current_user):
    """
    Retorna recomendações personalizadas do Spotify para o usuário.
    """
    suggestions = SpotifyService.get_suggestions(current_user)
    
    return success_response(
        data=suggestions,
        message="Sugestões recuperadas."
    )

@me_bp.route('/monthly-title', methods=['POST'])
@require_auth
def set_monthly_title(current_user):
    """
    Define ou atualiza o título de um mês específico.
    Payload esperado: {"month": 5, "year": 2026, "title": "A Fase do Jazz"}
    """
    payload = request.json
    month = payload.get('month')
    year = payload.get('year')
    title = payload.get('title')

    # Validação crua antes de mandar pro service
    if not month or not year or title is None:
        raise BusinessRuleError("Parâmetros 'month', 'year' e 'title' são obrigatórios no JSON.")

    meta = MetaService.set_monthly_title(current_user.id, int(month), int(year), str(title).strip())
    
    return success_response(
        data=meta.to_dict(),
        message="Título do mês atualizado com sucesso!"
    )

@me_bp.route('/monthly-title/generate', methods=['POST'])
@require_auth
def generate_my_title(current_user):
    """Gera automaticamente o título do mês baseado no gosto musical."""
    payload = request.json or {}
    month = payload.get('month')
    year = payload.get('year')

    if not month or not year:
        raise BusinessRuleError("Mês e ano são necessários.")

    meta = MetaService.generate_automatic_monthly_title(
        user_id=current_user.id, 
        month=int(month), 
        year=int(year)
    )

    return success_response(
        data=meta.to_dict(),
        message=f"Título '{meta.title}' gerado com sucesso!"
    )