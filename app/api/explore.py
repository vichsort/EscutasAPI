from flask import Blueprint
from app.utils import success_response
from app.services.explore_service import ExploreService

explore_bp = Blueprint('explore', __name__, url_prefix='/api/explore')

@explore_bp.route('/trending', methods=['GET'])
def get_trending():
    """Álbuns em alta na comunidade."""
    data = ExploreService.get_trending_albums()
    return success_response(data=data, message="Álbuns em alta recuperados.")

@explore_bp.route('/hall-of-fame', methods=['GET'])
def get_hall_of_fame():
    """Os álbuns mais bem avaliados de todos os tempos."""
    data = ExploreService.get_hall_of_fame()
    return success_response(data=data, message="Hall da fama recuperado.")

@explore_bp.route('/feed', methods=['GET'])
def get_global_feed():
    """Feed de reviews recentes da comunidade."""
    data = ExploreService.get_global_feed()
    return success_response(data=data, message="Feed global recuperado.")

@explore_bp.route('/top-reviewers', methods=['GET'])
def get_top_reviewers():
    """Usuários mais ativos da semana."""
    data = ExploreService.get_top_reviewers()
    return success_response(data=data, message="Top avaliadores recuperados.")